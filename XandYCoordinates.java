public class XandYCoordinates {
  
  public int height; // height coordinate of the image
  public int width; // width coordinate of the image
  
  public XandYCoordinates(int height, int width) {
    this.height = height;
    this.width = width;
  }
  
  @Override
  public boolean equals(Object object) {
    if (object instanceof XandYCoordinates)
      if (this.height == ((XandYCoordinates) object).height && this.width == ((XandYCoordinates) object).width)
        return true;
    return false;
  }
}
