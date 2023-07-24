# CutView
CutView is a GUI that relieves the tedious process of getting pixel intensity data from images and data values from NetCDF files along a line. This simplifies the analysis of satellite imagery or other images with linear features where the brightness of the pixel can be used to gauge some physical value. Examples include measuring sea ice floe concentration or characterizing ice sheet fractures. For NetCDF files, CutView serves as an easy way to view datasets and extract data from linear features. CutView is designed to make the measurement of linear features as automatic as possible through “marker” tools where linear features can be marked out and have transects automatically be made across. Multiple features can be marked at once on a file and saved all together as a “project” that can be reuploaded and continued or edited. This is invaluable for images such as the figure below where there are a multitude of features that could be analyzed.


![](gui_demo.png)

The program will display a plot of the data as well as package the data into a downloadable JSON file. When extracting values from the image/dataset, the program uses linear interpolation to interpolate between the values of the pixels to ensure the most accurate portrayal of the line drawn. 

Please refer to the repo wiki for installation and usage instructions.
