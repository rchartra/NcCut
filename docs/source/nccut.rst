NcCut API Reference
=====================

This section serves as reference for contributors who are looking to understand **NcCut's** underlying structure. This is not a user facing API.

nccut.nccut module
----------------------

Builds app and sets initial window.

Creates the widget tree and sets the initial window size. To load app, run ``NcCut().run()``

.. py:class::  nccut.nccut.NcCut(**kwargs)

    Bases: :class:`App`

    Builds app and widget tree.

    Creates the initial window and ensures font sizes in the app update uniformly
    when the window resizes.

    .. py:method:: build()

       Override App class build method and return widget tree.

       :return: Root of widget tree.

    .. py:method:: on_resize(*args)

       Triggers font adjustments when the window size is adjusted.

       :param \*args: Accepts args :class:`App` class supplies though they aren't needed.

    .. py:method:: on_start()

       Sets initial window size according to operating system.

nccut.dropdowns module
------------------------

.. automodule:: nccut.dropdowns
   :members:
   :undoc-members:
   :show-inheritance:

nccut.filedisplay module
--------------------------

.. automodule:: nccut.filedisplay
   :members:
   :undoc-members:
   :show-inheritance:

nccut.functions module
------------------------

.. automodule:: nccut.functions
   :members:
   :undoc-members:
   :show-inheritance:

nccut.homescreen module
-------------------------

.. automodule:: nccut.homescreen
   :members:
   :undoc-members:
   :show-inheritance:

nccut.marker module
---------------------

.. automodule:: nccut.marker
   :members:
   :undoc-members:
   :show-inheritance:

nccut.markerwidth module
--------------------------

.. automodule:: nccut.markerwidth
   :members:
   :undoc-members:
   :show-inheritance:

nccut.multimarker module
--------------------------

.. automodule:: nccut.multimarker
   :members:
   :undoc-members:
   :show-inheritance:

nccut.multitransect module
----------------------------

.. automodule:: nccut.multitransect
   :members:
   :undoc-members:
   :show-inheritance:

nccut.netcdfconfig module
---------------------------

.. automodule:: nccut.netcdfconfig
   :members:
   :undoc-members:
   :show-inheritance:

nccut.plotpopup module
------------------------

.. automodule:: nccut.plotpopup
   :members:
   :undoc-members:
   :show-inheritance:

nccut.singletransect module
-----------------------------

.. automodule:: nccut.singletransect
   :members:
   :undoc-members:
   :show-inheritance:
