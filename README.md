# GPSIO Extension

(This is the text from gpsio.caltopo.com - GPSIO has since been transfered to github in the NCSSAR organizational account.)

GPSIO is a still-experimental replacement for the Garmin Communicator plugin, built on open web standards and using GPSBabel to read GPS data. Supported browsers are Chrome and Firefox. Supported OSs are Mac, Windows and (soon) Linux.

## Installing the GPSIO Extension
For the time being, GPSIO installation is a multi-step process that requires a bit of computer savvy. Hopefully, at some point in the future, this will all get boiled down to a single-click install.

### Install the prerequisites if not already installed on your computer:
1. Python, which comes pre-installed on Mac and Linux installations, but may need to be installed for Windows. Click [here](https://www.python.org/downloads/) to download the latest Python for windows. During installation, make sure to enable the option to "Add Python to environment variables" (or similar wording) so that other programs can make use of it. If needed, you can run the install program again, and modify your existing Python installation, to enable that option.
2. GPSBabel, an open source program for working with GPSs and GPS data (consider making a donation). Click [here](http://www.gpsbabel.org/download.html) to download.
3. For Windows: the latest Garmin USB drivers, available [here](https://www8.garmin.com/support/download_details.jsp?id=591). For USB-mode devices (Garmin 60 or similar non-mass-storage-mode devices), you can run Windows Device Manager to verify the driver installation: if the drivers are installed properly, a plugged-in Garmin USB-mode device will show up in a category named "Garmin Devices"; if the drivers are not installed, a plugged-in Garmin USB-mode device will show up as "Unknown USB Device", causing CalTopo GPSIO transfers to abort with a red line of text indicating that no GPS was found. (Mass-storage-mode devices such as Garmin 62, 64, etc. will instead show up under 'Drives' and/or 'Portable Devices'.)

## To comply with browser security restrictions, GPSIO is composed of two parts: an extension and a host. You need to install both parts.
1. Install the host. [Download.](http://gpsio.caltopo.com/gpsio-installer.zip) On windows systems you must unzip this file by right-clicking on it and choosing "Extract All"; the installer will not work properly if you navigate into the zipped folder by double-clicking on it in the windows file explorer. Either double-click on the install.py script or open up a command prompt and run "python installer.py".
2. Install the extension in your browser.
- Chrome:
    - Click either of the following links to install the extension
        - [Works on all websites](https://chrome.google.com/webstore/detail/gpsio/afgcejeehpnhafgikkimogllebbgegck)
        - [Restricted to CalTopo/SARTopo](https://chrome.google.com/webstore/detail/gpsio/hoecjlpnaeogdncffnambjemmfcajmcc)
    - Click "Add to Chrome"
- Firefox:
    - Click [here](http://gpsio.caltopo.com/gpsio.xpi) to install the extension
    - Click "Allow"


# Importing GPS Tracks and Waypoints as Lines and Markers using GPSIO
1. Connect the GPS to the computer with a USB cable. It may take the GPS a minute or two to save the tracks and establish a connection.
2. On the CalTopo top menu bar, click "Import" and "Connect via GPSIO".
3. A message will appear while the GPS is being read.
4. If the connection is unsuccessful, you may see an error message. The extension may not be correctly installed, or you may have not given the GPS long enough to connect.
5. A second message will appear once the data has been read and is being processed.
6. Un-check any waypoints or tracks you do not want to import and click "Import".
6. Track will appear in the "Lines & Polygons" folder, waypoints will appear in the "Markers" folder.

# Exporting Lines, Polygons and Markers to GPS Units using GPSIO
1. Connect the GPS to the computer with a USB cable. It may take the GPS a minute or two to save the tracks and establish a connection.
2. On the CalTopo top menu bar, click "Export" and "Connect via GPSIO".
3. Un-check any objects you do not want to import and click "Export".
4. Once the export is complete, you will see this message:
5. If the connection is unsuccessful, you may see an error message. The extension may not be correctly installed, or you may have not given the GPS long enough to connect.


## Contributing
GPSIO is free software (GPL) and is hosted at https://github.com/ncssar/gpsio. Contributions are welcome; two high priority items are Linux installation support and integration with non-Garmin GPSs (either through auto-detection or a user-selectable GPS type dropdown). Testing with additional GPS units is also valuable; send bug reports to info@caltopo.com.

## Troubleshooting / debugging - IN PROGRESS
You tried to install GPSIO but it's not working... what now?  Troubleshooting GPSIO is tricky because it has multiple parts.  Here are some troubleshooting guidelines:
1. Do you see the GPSIO extension icon (currently, an odd squished blue-and-gray thing that is supposed to look like an old GPS) at the top right of your browser window, alongside any other extension icons?
    YES: go to the next step
    NO: the browser extension (Chrome or Firefox) hasn't been installed; see the installation steps above.  If that doesn't solve it, contact the developer with these details.
2. Left-click the GPSIO extension icon.  A small popup box should appear near the extension icon.  Does it have a red line of text that says 'Cannot communicate with host', or, a green line of text that says 'Plugin working properly' with a selection of filter options?
    RED: left-click 'check again' once or twice.  If the red line doesn't go away, go to the next step.
    GREEN: contact the developer with exact details of the error you're seeing.
3. Open a command terminal, go to the default gpsio installation directory (normally, the 'gpsio' directory under your user home directory), and run wrapper.py using python.
