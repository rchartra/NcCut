CutView API Reference
=====================

This section serves as reference for contributors who are looking to understand **CutView's** underlying structure. This is not a user facing API.

cutview.cutview module
----------------------

Builds app and sets initial window.

Creates the widget tree and sets the initial window size. To load app, run ``CutView().run()``

.. py:class::  cutview.cutview.CutView(**kwargs)

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

cutview.dropdowns module
------------------------

.. automodule:: cutview.dropdowns
   :members:
   :undoc-members:
   :show-inheritance:

cutview.filedisplay module
--------------------------

.. automodule:: cutview.filedisplay
   :members:
   :undoc-members:
   :show-inheritance:

cutview.functions module
------------------------

.. automodule:: cutview.functions
   :members:
   :undoc-members:
   :show-inheritance:

cutview.homescreen module
-------------------------

.. automodule:: cutview.homescreen
   :members:
   :undoc-members:
   :show-inheritance:

cutview.marker module
---------------------

.. automodule:: cutview.marker
   :members:
   :undoc-members:
   :show-inheritance:

cutview.markerwidth module
--------------------------

.. automodule:: cutview.markerwidth
   :members:
   :undoc-members:
   :show-inheritance:

cutview.multimarker module
--------------------------

.. automodule:: cutview.multimarker
   :members:
   :undoc-members:
   :show-inheritance:

cutview.multitransect module
----------------------------

.. automodule:: cutview.multitransect
   :members:
   :undoc-members:
   :show-inheritance:

cutview.netcdfconfig module
---------------------------

.. automodule:: cutview.netcdfconfig
   :members:
   :undoc-members:
   :show-inheritance:

cutview.plotpopup module
------------------------

.. automodule:: cutview.plotpopup
   :members:
   :undoc-members:
   :show-inheritance:

cutview.singletransect module
-----------------------------

.. automodule:: cutview.singletransect
   :members:
   :undoc-members:
   :show-inheritance:
