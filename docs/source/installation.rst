Installation
============

**NcCut** can be downloaded directly from PyPI using PIP:

#. It is recommended to first create a virtual environment before installing packages on your system to prevent package compatibility issues. From the terminal at your desired directory use:

    * For Linux and Mac:

        .. code-block:: console

            python3 -m venv nccut-venv
            source nccut-venv/bin/activate

    * For Windows:

        .. code-block:: console

            python -m venv nccut-venv
            nccut-venv\Scripts\activate

#. Then install NcCut using PIP:

    .. code-block:: console

        pip install nccut

#. To run the app there are two options:

    * From the command Line:

        .. code-block:: console

            nccut

        You can also pass a NetCDF or image file directly into the app via the command line:

        .. code-block:: console

            nccut -file file_name

    * From Python:

        .. code-block:: python

            from nccut.nccut import NcCut
            NcCut().run()
    .. note::
       The first run after installation may be slow as underlying packages must unpack and compile. Future runs should open much quicker.
#. To exit the virtual environment when finished:

    .. code-block:: console

        deactivate

#. To open the same virtual environment again in the future:

    * For Linux and Mac:

        .. code-block:: console

            source nccut-venv/bin/activate

    * For Windows:

        .. code-block:: console

            nccut-venv\Scripts\activate

Troubleshooting
---------------

* You will need to have python of version *at least 3.9* installed on your computer
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
