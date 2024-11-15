import flask 
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re
from PIL import Image 
import os
import sqlite3
import subprocess
import io
import json
from collections import deque
import numpy as np 
from PIL import Image as im 

app = flask.Flask("my application")

@app.route('/')
def home():
    
    # The homepage just reads the index file
    # no further processing required
    
    with open("index.html") as f:
        html = f.read()
    return html

@app.route('/map.html', methods=["POST", "GET"])
def mapping():
    
    # read all the query strings
    query_string = dict(flask.request.args)
    
    building = query_string['building']
    floor = query_string.get('floor')
    
    if flask.request.method == 'GET':
        
        # connecting to the database which contains information about all the floor plans 
        conn = sqlite3.connect("database.db")
        
        # using the database to get all the floors in the building
        query_str = f'''SELECT distinct(floor) AS floor
        FROM big_table 
        WHERE building == "{building}"'''
        df = pd.read_sql(query_str, conn)
        conn.close()

        # creating floor options for the page
        floors = sorted(list(set(df['floor'])))
        
        # if there is no information about the building in database, redirect back to home
        if len(floors) == 0:
            return flask.Response("""
            Please select a different building. 
            Redirecting back to the homepage in 5 seconds.""", headers = {"Refresh": "5; url=/"})
        
        # creating floor options for the page
        floor_html = [f"<option value='{floor}'>{floor}</option>" for floor in floors]
        rep_floor = "".join(floor_html)

        # render the final html page
        with open("floorpage.html") as f:
            html = f.read()
            
        # adding the options for the floors
        html = html.replace("BUTTONSFLOOR", rep_floor)
        html = html.replace('????',building)

        return html

    # the url is visited using the POST method only through the form
    # when we reach this point, the source and destination will be chosen
    # no source or no destination is not an option
    if flask.request.method == 'POST':
        
        # to be used to determine when to display the result
        result_flag = True
   
        if floor == None:
            # if floor was not known so far, get it from the form
            floor = flask.request.form.get('flr')
            # if we just found out about the floor,
            # we need to get more information before going to the results page
            result_flag = False
                
        # if the result flag is not set
        if not result_flag:
            
            conn = sqlite3.connect("database.db")
   
            # get the list of rooms on the floor
            query_str = f'''SELECT text
            FROM big_table 
            WHERE building == "{building}" AND floor == "{floor}"'''
            df = pd.read_sql(query_str, conn)

            conn.close()
            
            # creating options of the rooms for source and destination
            options = sorted(list(df['text']))
            option_html = [f"<option value='{option}'>{option}</option>" for option in options]
            rep = "".join(option_html)        

            
            with open('map.html') as f:
                html = f.read()
            html = html.replace('###', building)
            
            # adding options for the source and destination
            html = html.replace("BUTTONS1", rep)
            html = html.replace("BUTTONS2", rep)
            html = html.replace('????',building+f'&floor={floor}')

            return html
        
        
        # get the source and destination from the form
        src = flask.request.form['src2']
        dst = flask.request.form['dst2']

        # extract the coordinates for the room from the database
        conn = sqlite3.connect("database.db")

        query_str = f'''SELECT *
        FROM big_table 
        WHERE building == "{building}" AND floor == "{floor}" AND (text == {src} OR text == {dst})'''
        df = pd.read_sql(query_str, conn)
        df = df.set_index('text')

        conn.close()
        
        print(df)
        
        if type(df.loc[src]) == pd.DataFrame:
            src1 = str(int(df.loc[src]["top"].iloc[0])) 
            src2 = str(int(df.loc[src]["left"].iloc[0]))
        else:
            src1 = str(int(df.loc[src]["top"])) 
            src2 = str(int(df.loc[src]["left"]))
            
            
        if type(df.loc[dst]) == pd.DataFrame:
            dst1 = str(int(df.loc[dst]["top"].iloc[0]))
            dst2 = str(int(df.loc[dst]["left"].iloc[0]))
        else:
            dst1 = str(int(df.loc[dst]["top"]))
            dst2 = str(int(df.loc[dst]["left"]))
     
        
        # this is the file name for the image files in the floorplans directory
        fname = building+"_"+floor+".jpg"
                
        # filename, source coordinate y, source x, destination y, destination x (x and y according to pixels not normal cartesian)
        path = subprocess.run(['java', 'AStarGraph', os.path.join('floorplans', building, fname), src1, src2, dst1, dst2], stdout=subprocess.PIPE).stdout
        
        print(path)
        
        path = str(path, encoding='utf-8')
        outs = path.split("\n")
        paths = outs[0]

        
        with open("temp.txt", "w") as f:
            f.write(paths)
        
        print(src,dst)
        
        with open('result.html') as f:
            data = f.read()
            
        data = data.replace('??', fname)
        data = data.replace('###', building)

        return data
    
    
# this route is visited from the result page only
# it will always have a query string with the filename and directory
# directory name is the building name
# files are for specific floors
@app.route('/dashboard.png')
def dashboard():
    query_string = dict(flask.request.args)
    fname = query_string['fname']
    dirs = query_string['dir']
    
    with open("temp.txt") as f:
        data = f.read()
    l = re.findall('\(\d+,\d+\)', data)
    l2 = [item[1:-1].split(',') for item in l]
    l3 = [(int(item[0]), int(item[1])) for item in l2]
       
    print(os.path.join('floorplans', dirs, fname))
    
    # plotting the image on a plot
    # using this method so that the numpy array can be edited with the results
    img = plt.imread(os.path.join('floorplans', dirs, fname))
    
    img2 = np.zeros((3,img.shape[1],img.shape[0]), dtype=int)
    img2[0] = img.transpose()
    img2[1] = img.transpose()
    img2[2] = img.transpose()
    img3 = img2.transpose()  
        
    
    for y,x in l3:
        img3[x][y] = [255,0,0]
        img3[x+1][y] = [255,0,0]
        img3[x][y+1] = [255,0,0]
        img3[x+1][y+1] = [255,0,0]
        img3[x+2][y] = [255,0,0]
        img3[x][y+2] = [255,0,0]
        img3[x+2][y+2] = [255,0,0]
        img3[x+3][y] = [255,0,0]
        img3[x][y+3] = [255,0,0]
        img3[x+3][y+3] = [255,0,0]


    
    figure = plt.figure()
    axes = figure.add_subplot(111)
    axes.imshow(img3)

    # using a fake file to temporarily store the image in the right format
    f = io.BytesIO() 
    figure.savefig(f, format='svg')
    plt.close()
    
    return flask.Response(f.getvalue(), headers = {"Content-Type":"image/svg+xml"})


# the generic image display route for displaying images
# needs a preexisting image in the website-images directory
@app.route('/image')
def dash2():
    query_string = dict(flask.request.args)
    fname = query_string['fname']
#     dirs = query_string['dir']
    ext = fname.split('.')[-1]
    path = os.path.join('website-images', fname)
    print(path)
    
    with open(os.path.join('website-images', fname), "rb") as f:
        return flask.Response(f.read(), headers = {"Content-Type":f"image/{ext}"})



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, threaded=False, port=8000)
