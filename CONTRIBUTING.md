# Contributions to CutView

Contributions are welcome! Feel free to add features, tests, examples, suggestions, whatever the like but please follow 
the following guidelines to smooth the process.

## Testing and Submissions

- Please submit a pull request for any additions. Any additions will be automatically tested upon submission through github actions.
- If you are adding significant features to the GUI please include tests similar to those found in the [testing](old_versions/old_t3st_app.py) file to ensure backwards compatibility with the GUI.
- Please include instructions on how to use your feature to add to the wiki. You can submit these as part of you pull request or as a GitHub issue. If your contribution is approved I will add your
instructions to the existing wiki.

## Code style

- Please follow [PEP-8]( <https://www.python.org/dev/peps/pep-0008/>) standards as much as possible, though readibility and consistency are paramount.

## Issues

- Please submit any bugs or issues with the GUI through GitHub issues.
- Include as much information as possible such as your operating system, python version, and <ins>**steps to reproduce the issue**</ins>.
- If possible, include the file you are using with the viewer.

# Tips for Adding New Tools

## Recommended Resources:

- If you are new to object oriented programming, I highly recommend having a good understanding of [python classes](<https://docs.python.org/3/tutorial/classes.html>) before attempting to add your own code.
- Refer to the [Kivy documentation](<https://kivy.org/doc/stable/guide/widgets.html>). The Kivy python library is the backbone for all UI related aspects of this app, therefore knowing how it works and how to use it is essential for making any additions or changes.  

## Tips for adding a new tool button

- Graphically, sidebar tool buttons should be added in the `cutview.kv` file in the same manner and place as the current tool buttons. 
- Bind `root.transect_btn(“_YOUR_TOOL_ID_”)` to your button, which will call the corresponding method from the homescreen. With this method you can control how your widget is added and cleaned up. 
- Tools are added as children to the existing `ImageView` object, which is the image you can click and drag around. 
- When a tool is created, buttons for a “drag mode” and an “edit mode” are added to the sidebar. When drag mode is selected, clicking on the image should only move the image around, not perform any action with the tool. Your tool should have a `change_dragging()` method to pause anything your tool is doing. Calling the method again should unpause your tool
- Editing mode will also put the app in dragging mode, however editing mode will additionally add buttons “Delete Last Line” and “Delete Last Point” to the sidebar. If these don’t make sense with your tool you can choose to not add an edit button by editing the `transect_btn()` method. Otherwise your tool must have a `del_line()` and `del_point()` method, respectively.
- I recommend passing a reference to the home screen to your tool class upon creation. This allows you to access methods within the home class, the entire app widget tree, and the current NetCDF or image data.
- Image data is stored in the home screen’s `rgb` attribute once an image has been loaded.
- A dictionary storing the active NetCDF data and information about the active data is stored in the home screen’s `netcdf` attribute.
- Pressing the tool button after the tool was created should clear the tool off the screen, which is how `transect_btn()` is already set up. If you’d like to create multiple objects, please add a new button to do so to the sidebar (see the `MultiMarker` class for an example).
- If you’d like to use the plotting popup menu for your tool’s output data simply call for popup as such: `PlotPopup(_your_data_dict_, _home_reference_)`. However, unless your data structure matches the data structure of the current two tools, you’ll have to edit/add to the `PlotPopup` code to work with your tool’s output data. Here are some tips:
  - If you’d like to add more selection menus or buttons, do so in the `__init__` method of the class. Follow the example of the current menus and you should get pretty far. 
  - Edit `get_data()` to change how `active_data` is updated by the selection menus 
  - Edit `plot_active()` to change how the `active_data` is plotted. This method mostly just sets up the creation of subplots for each variable the user has selected. For each individual variable plot look at the `plot_single()` method


## Support

- If you otherwise require assistance contact rchartra@uw.edu. I'm happy to answer any questions.
