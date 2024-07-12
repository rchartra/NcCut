Contribution Guide
==================

Contributions are welcome! Feel free to add new features, unit tests, documentation, examples, whatever you think would improve the app. However please follow the following guidelines to ensure a smooth contribution process.

Submission
----------
* To report a bug, submit an issue on `GitHub issues <https://github.com/rchartra/CutView/issues>`_. Please include as much information as possible including your operating system, python version, and steps required to reproduce the issue. If possible, attach the file you are using with the viewer as well.
* To suggest new features or functionality changes please also submit an issue on `GitHub issues <https://github.com/rchartra/CutView/issues>`_.
* To submit new features or changes to the code please submit a pull request on `GitHub <https://github.com/rchartra/CutView/pulls>`_ to the main branch from your forked repository. Submissions will be automatically tested and then manually reviewed to ensure compatibility.

Testing
-------
* If you are adding new features to the GUI please write unit tests for your feature. You may refer to the existing test `suite <https://github.com/rchartra/CutView/tree/master/tests>`_ for examples on how to write them.
* Unit tests ensure that any future changes to the GUI won't break your code making them crucial to maintaining this project long term.
* When writing unit tests, check only that the expected user input results in the correct final behavior. Tests that look too deep into how the code itself works are vulnerable to failing over small changes even if the code overall is working correctly.
* Please also rigorously test your feature as you are developing it. There should be no way for the app to crash while it's in use. If there is a way for a user to do something incorrectly, (for example entering an invalid file name), handle that case and alert the user via :py:func:`cutview.functions.alert`.

Documentation
-------------
* If you are adding a new feature please add instructions as to how to use your tool to the the documentation.
* To update the documentation edit the reStructuredText files in the docs `source <>`_ folder.
* Your code should be well documented with docstrings according to the Google python style `guide <https://google.github.io/styleguide/pyguide.html>`_. The docstrings are used to create the :doc:`cutview` section of the docs, so please ensure they are properly formatted.

Code Style
__________

* Please follow `PEP-8 <https://peps.python.org/pep-0008/>`_ standards as much as possible, though readability and consistency are paramount. Two exceptions are standards E402 and E501. Please keep code line length less than or equal to 120 characters.

Tips for Adding a New Tool
--------------------------

* Refer to the `Kivy documentation <https://kivy.org/doc/stable/guide/widgets.html>`_. The Kivy python library is the backbone for all UI related aspects of this app, therefore knowing how it works and how to use it is essential for making any additions or changes.
* Read through the :doc:`cutview`. This will give you an understanding of the widget tree structure and then you can use the code for the **Transect** and **Transect Marker** tools as examples for how to structure your tool to work with the GUI.

    * In summary, the Homescreen object serves as the root. The root creates the FileDisplay object with the correct image to display. The FileDisplay object then manages setting changes and the tools. The tools are added as children of the FileDisplay object. The tools add a **Plot** button to the sidebar which calls for a PlotPopup object which allows the user to view and save their data.

* To add a button for your tool in the sidebar edit the `cutview.kv <https://github.com/rchartra/CutView/blob/master/src/cutview/cutview.kv>`_ file and follow the example of the current tools.
* You should pass a reference to the home screen to your tool class upon creation. The home screen is the root of the widget tree, so doing this will allow you to access the rest of the widget tree.
* The home screen has a reference to the active :py:func:`cutview.filedisplay.FileDisplay` object. This is what holds the loaded image and tools when they are created. You should add your tools as children to this object via the :py:func:`cutview.filedisplay.FileDisplay.manage_tool()` method.
* You can access the loaded data as well as the user selected configurations in the :py:func:`cutview.filedisplay.FileDisplay.config` attribute.
* You should have a ``font_adapt(self, font)`` method which accepts a font and updates the font you use anytime there is text involved in your tool. Otherwise when the user changes the size of the window the font size of your tool will not update with the rest of the widgets.
* When a tool is created, buttons for a **Drag Mode** and an **Edit Mode** are added to the sidebar. Your tool should have a drag mode. When drag mode is selected, clicking on the image should only move the image around, not perform any action with the tool. Your tool should have a ``change_dragging()`` method to pause anything your tool is doing as well as a ``dragging`` boolean attribute to indicate whether or not it is in dragging mode. Calling the method again should unpause your tool
* Editing mode will also put the app in dragging mode, however editing mode will additionally add buttons “**Delete Last Line** and **Delete Last Point** to the sidebar. If these don’t make sense with your tool you can choose to not add an edit button by editing the :py:func:`cutview.filedisplay.FileDisplay.manage_tool()` method. Otherwise your tool must have a ``del_line()`` and ``del_point()`` method.
* If you’d like to create a plotting popup menu for your tool’s output data you can either edit the :py:func:`cutview.plotpopup.PlotPopup` code to work with your data or use :py:func:`cutview.plotpopup.PlotPopup` as an example and create a new popup class for your tool. Unless your tool is very similar to the two current tools I recommend the latter.


.. toctree::
   :maxdepth: 4

   cutview
