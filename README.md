# GPS I/O Extension

(This is the text from gpsio.caltopo.com - GPSIO has since been transfered to github in the NCSSAR organizational account.)

GPSIO is a still-experimental replacement for the Garmin Communicator plugin, built on open web standards and using GPSBabel to read GPS data. Supported browsers are Chrome and (soon) Firefox. Supported OSs are Mac, Windows and (soon) Linux.

## Dependencies
Python, which comes pre-installed on Mac and Linux installations, but may need to be installed for Windows
GPSBabel, an open source program for working with GPSs and GPS data (consider making a donation).

## Installing the GPSIO Extension
For the time being, GPSIO installation is a multi-step process that requires a bit of computer savvy. Hopefully, at some point in the future, this will all get boiled down to a single-click install.

### Install the prerequisites if not already installed on your computer:
1. Python, which comes pre-installed on Mac and Linux installations, but may need to be installed for Windows. Click here to download the latest Python for windows. During installation, make sure to enable the option to "Add Python to environment variables" (or similar wording) so that other programs can make use of it. If needed, you can run the install program again, and modify your existing Python installation, to enable that option.
2. GPSBabel, an open source program for working with GPSs and GPS data (consider making a donation). Click here to download.
3. For Windows: the latest Garmin USB drivers, available here. For USB-mode devices (Garmin 60 or similar non-mass-storage-mode devices), you can run Windows Device Manager to verify the driver installation: if the drivers are installed properly, a plugged-in Garmin USB-mode device will show up in a category named "Garmin Devices"; if the drivers are not installed, a plugged-in Garmin USB-mode device will show up as "Unknown USB Device", causing CalTopo GPSIO transfers to abort with a red line of text indicating that no GPS was found. (Mass-storage-mode devices such as Garmin 62, 64, etc. will instead show up under 'Drives' and/or 'Portable Devices'.)

## To comply with browser security restrictions, GPSIO is composed of two parts: an extension and a host. You need to install both parts.
1. Install the host. Download. On windows systems you must unzip this file by right-clicking on it and choosing "Extract All"; the installer will not work properly if you navigate into the zipped folder by double-clicking on it in the windows file explorer. Either double-click on the install.py script or open up a command prompt and run "python installer.py".
2. Install the extension in your browser.
- Chrome:
-- Click either of the following links to install the extension
--- Works on all websites
--- Restricted to CalTopo/SARTopo
-- Click "Add to Chrome"
- Firefox:
-- Click here to install the extension
-- Click "Allow"

## Contributing
GPSIO is free software (GPL) and is hosted at https://github.com/ncssar/gpsio. Contributions are welcome; two high priority items are Linux installation support and integration with non-Garmin GPSs (either through auto-detection or a user-selectable GPS type dropdown). Testing with additional GPS units is also valuable; send bug reports to info@caltopo.com.
