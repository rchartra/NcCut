Installation
============

**CutView** can be downloaded directly from PyPI using PIP:

#. It is recommended to first create a virtual environment (if your IDE does not do it for you) before installing packages on your system to prevent package compatibility issues. From the terminal at your desired directory use:

    * For Linux and Mac:

        .. code-block:: console

            python3 -m venv venv
            source venv/bin/activate

    * For Windows:

        .. code-block:: console

            python3 -m venv venv
            venv\Scripts\activate

#. Then install CutView using PIP:

    .. code-block:: console

        pip install cutview

#. To run the app execute the following Python code:

    .. code-block:: python

        from cutview.cutview import CutView
        CutView().run()

#. To exit the virtual environment when finished:

    .. code-block:: console

        deactivate

#. To open the same virtual environment again in the future:

    * For Linux and Mac:

        .. code-block:: console

            source venv/bin/activate

    * For Windows:

        .. code-block:: console

            venv\Scripts\activate

Troubleshooting
---------------

* You will need to have python of version at least 3.9 installed on your computer
* Ensure you have X11 on your computer (not always the case on Macs)
* There is occasionally a bug with the way kivy accesses it's dependencies. If the app won't run for you try running these lines in the terminal:

    .. code-block:: console

        pip uninstall kivy kivy.deps.sdl2 kivy.deps.glew kivy.deps.gstreamer image
        pip install --upgrade pip wheel setuptools
        pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew --extra-index-url https://kivy.org/downloads/packages/simple/
        pip install kivy

Support
-------

Stuck? Reach out to rchartra@uw.edu
