# Contributions to CutView

Contributions are welcome! Feel free to add features, tests, documentation, examples, whatever you think would improve the app. However please follow 
the following guidelines to ensure a smooth contribution process.

## Testing and Submissions

- Please submit a pull request for any additions or changes. Any submissions will be automatically tested upon submission through github actions and then manually reviewed.
- If you are adding significant features to the GUI please perform rigorous testing before submission. There should be no way for the app to crash when the user uses the app. Instead, there should be an alert banner notifying the user as to what they did wrong. You should also include unit tests similar to those found in the existing test suite to ensure backwards compatibility with the GUI later on.
- Please include detailed instructions on how to use your feature to add to the documentation. You can submit these as part of you pull request or as a GitHub issue. 

## Code style

- Please follow [PEP-8]( <https://www.python.org/dev/peps/pep-0008/>) standards as much as possible, though readibility and consistency are paramount. Two exceptions are standards E402 and E501. Please keep code line length less than or equal to 120 characters.
- Your code should be documented with docstrings. Please follow the guidelines of the docstrings section of the Google python style [guide](https://google.github.io/styleguide/pyguide.html)

## Issues

- Please submit any bugs or issues with the GUI through GitHub issues.
- Include as much information as possible such as your operating system, python version, and <ins>**steps to reproduce the issue**</ins>.
- If possible, include the file you are using with the viewer.

# Tips for Adding New Tools

## Recommended Resources:

- If you are new to object oriented programming, I highly recommend having a good understanding of [python classes](<https://docs.python.org/3/tutorial/classes.html>) before attempting to add your own code.
- Refer to the [Kivy documentation](<https://kivy.org/doc/stable/guide/widgets.html>). The Kivy python library is the backbone for all UI related aspects of this app, therefore knowing how it works and how to use it is essential for making any additions or changes.  

## Tips for adding a new tool

- Use the current "Transect" and "Transect Marker" tools as examples for how to structure your tool so that it can interact with the other features of the GUI.
- You should pass a reference to the home screen to your tool class upon creation. This allows you to access methods within the home class, the entire app widget tree, and the current NetCDF or image data.
- Graphically, sidebar tool buttons should be added in the `cutview.kv` file in the same manner and place as the current tool buttons. 
- Tools are added via the `manage_tool()` method of the existing `FileDisplay` object, which is the image you can click and drag around, as children of the object.
- The loaded data as well as relevant configuration settings are stored in the `config` attribute of the `FileDisplay` object.
- When a tool is created, buttons for a “drag mode” and an “edit mode” are added to the sidebar. Your tool should have a drag mode. When drag mode is selected, clicking on the image should only move the image around, not perform any action with the tool. Your tool should have a `change_dragging()` method to pause anything your tool is doing as well as a `dragging` boolean attribute to indicate whether or not it is in dragging mode. Calling the method again should unpause your tool
- Editing mode will also put the app in dragging mode, however editing mode will additionally add buttons “Delete Last Line” and “Delete Last Point” to the sidebar. If these don’t make sense with your tool you can choose to not add an edit button by editing the `manage_tool()` method. Otherwise your tool must have a `del_line()` and `del_point()` method.
- Pressing the tool button after the tool was created should clear the tool off the screen, which is how `manage_tool()` is already set up.
- If you’d like to create a plotting popup menu for your tool’s output data you can either edit the `PlotPopup` code to work with your data or use `PlotPopup` as an example and create a new popup class for your tool. Unless your tool is very similar to the two current tools I recommend the latter.

## Support

- If you otherwise require assistance contact rchartra@uw.edu. I'm happy to answer any questions.
