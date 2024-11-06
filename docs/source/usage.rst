Usage
=====

#. To install the app refer to the :doc:`installation` instructions.

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

For some example files to try out NcCut, refer to the :doc:`example` section.

Loading a File
--------------

**NcCut** supports .jpg, .jpeg, and .png image files and NetCDF .nc files.

#. To load the file you can either enter the absolute or relative path to your file in to the text box and select **Load*** or you can select **Browse** to find the file on your system.

    * If you are loading a NetCDF file a popup window will appear with additional selections:

        * Select which variable from your file you would like to see.
        * Confirm or select which dimensions you would like to use as the X and Y axes for your variable.
        * If your variable has data in a third dimension select the Z dimension and an initial Z value to display. You will be able to toggle between z values later.
        * At this time NcCut can only load variables with 2 or 3 dimensions.

#. You can scroll to zoom in and out of the image and can click and drag the image to move it around.

#. You can rotate or flip the image as well as change graphic settings for the tools using the buttons in the settings bar at the top of the screen.

#. If you are loading a NetCDF file, from the **NetCDF** menu in the settings bar you can change which variable or z value you'd like to see as well as change the color map or contrast of the image.

    * Changing the contrast and colormap only affects the displayed image. Transect data is taken from the NetCDF file itself.

Tools
-----

**NcCut** has two types of tools for making transects.

The :ref:`Transect Marker <transect_marker>` tool allows you to draw a line along a feature, and transects will be automatically made orthogonal to the line you've drawn with a set width:

    .. image:: _media/transect_marker.png

The :ref:`Transect Chain <transect_chain>` tool allows you to draw multiple transects chained together along a feature.

    .. image:: _media/transect_chain.png

.. _transect_chain:

Transect Chain
^^^^^^^^^^^^^^

Using this tool chains of transects can be drawn. Transects will be taken along the line segments drawn between the clicked points. Multiple such *Chains* can be drawn out at once before being plotted.

#. Hit the **Transect Chain** button to enter transect mode.
#. Click points along the feature you'd like to make transects along. Transects will be made between the points you click.
    * Select **Drag Mode** from the actions sidebar to drag the image without selecting points, and select **Transect Mode** to go back.
    * Select **Edit Mode** to delete either the last point clicked or the last chain drawn.
#. Double click the final point or select **New Chain** to begin a new chain and repeat for as many chains as you'd like.
#. When done select the **Plot** button and a popup will appear with a plot of all transects from the first chain and downloading options.

.. _transect_marker:

Transect Marker
^^^^^^^^^^^^^^^

Using this tool multiple *Markers* can be drawn onto a loaded file. These *Markers* can all be saved together as a *project* and reloaded into the viewer later. When a large file is being explored this allows you to mark out features over multiple sessions.

#. Hit the **Transect Marker** button to enter transect mode.
#. Click points along the feature you'd like to make transects across. Dots will appear on either side of the line drawn indicating the start and end points of the transects that will be made.

    * Select **Drag Mode** from the actions sidebar to drag the image without selecting points, and select **Transect Mode** to go back.
    * Select **Edit Mode** to delete either the last point clicked or the last marker drawn.
    * To change the width of the transects being made you may enter the number of pixels into the **Width** text box. Select **Set** to change the width for all future transects.

        * This will not change the width of transects already drawn
        * The default width is 40 pixels, you can enter any width within 0 and 400
        * If you change the width of a marker any new markers will continue to use that same width unless you change it again.

#. Double click the final point or select **New Marker** to begin a new marker and repeat for as many markers as you'd like.
#. When done select the **Plot** button and a popup will appear with a plot of all transects from the first marker and downloading options.

#. Click anywhere around the popup or the close button to dismiss

To upload a previously worked on project:

#. Load the same dataset/image you worked on previously. Project files are specific to the file, variable, and coordinate
selections originally used.
#. Hit the **Transect Marker** button to enter transect mode.
#. Instead of clicking new points, select the **Upload Project** button.
#. Enter the file name of the transect data you saved previously and select **Ok**.
#. All markers from the file will load onto the viewer and you can continue working on the project.

Plotting
--------

#. When you are finished using a tool, select the **Plot** button to view plots of your data and choose which data you would like to save.
    * You can select which chains/transects you'd like to plot
    * If you used the chain tool, the transects within the chain will be plotted continuously end to end
    * If you used the marker tool you can plot an average of the markers transects if you used the same marker width throughout the whole marker
#. If using a NetCDF file, more plotting selections are available to you
    * You can select multiple variables and Z values you'd like to see your selected chains/transects plotted from.
    * If using a NetCDF file with a Z dimension you can select **Plot all Z as Img** to plot an interactive image of a single chain/transect taken over all Z values of your dataset. To use this option select only one chain/transect and only one variable.
        * If you used the chain tool, the transects within the chain will be plotted continuously end to end

    .. image:: _media/nccutgraphic.png

#. You can save the current plot to .PNG or .PDF formats.
#. You can also save the transect data itself from three options:
    * **Save All Data** will save all transects from all markers or chains. If using a NetCDF file it will do so for the currently selected variables and z values.
    * **Save Selected Data** will save only the transects selected in the plotting menu. If using a NetCDF file it will do so for the currently selected variables and z values.
    * **Save All Z Values** will save all z values for the selected transects and variables. This option only appears if using a NetCDF file with three dimensions.
#. See the :ref:`Data Output <data_output>` section for how the saved data is formatted.
#. Click anywhere around the popup or the close button to dismiss plotting window.

.. _config_file:

Configuration File
------------------

NcCut's default graphic settings, netcdf configuration settings, and metadata can be configured using a configuration file. An example file with information on the possible configurations can be found `here <https://github.com/rchartra/NcCut/tree/main>`_.

For NcCut to locate the file it must be named ``nccut_config.toml`` and be in one of the following locations which are by ordered by decreasing search priority:

#. Command line argument:

    .. code-block:: console
        nccut -config path_to_config_file

#. Environment variable called 'NCCUT_CONFIG' holding the path to the config file.
#. Current working directory and then in
#. Either '%APPDATA%\nccut\nccut_config.toml' on Windows or '~/.config/your_app/config.toml' on Linux and macOS

Changing Logger Settings
------------------------

nccut.logger module
^^^^^^^^^^^^^^^^^^^^^

.. automodule:: nccut.logger
   :members:
   :undoc-members:
   :show-inheritance:
