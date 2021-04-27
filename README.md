# GPS I/O Extension

(This is the text from gpsio.caltopo.com - GPSIO has since been transfered to github in the NCSSAR organizational account.)

GPSIO is a still-experimental replacement for the Garmin Communicator plugin, built on open web standards and using GPSBabel to read GPS data. Supported browsers are Chrome and (soon) Firefox. Supported OSs are Mac, Windows and (soon) Linux.

## Dependencies
Python, which comes pre-installed on Mac and Linux installations, but may need to be installed for Windows
GPSBabel, an open source program for working with GPSs and GPS data (consider making a donation).

## Installation
To comply with browser security restrictions, GPSIO is composed of two parts: an extension and a host.

The host installer can be downloaded from the Code --> Download ZIP button on the main page of the GITHub project, or https://github.com/ncssar/gpsio/archive/refs/heads/master.zip. On windows systems you must unzip this file by right-clicking on it and choosing "Extract All"; the installer will not work properly if you navigate into the zipped folder by double- clicking on it in the windows file explorer. Either double-click on the install.py script or open up a command prompt and run "python installer.py".

The extension is installed through your browser.
Chrome comes in two versions: one that works on all websites, and one that is restricted to CalTopo/SARTopo
Firefox has a single version

## Contributing
GPSIO is free software (GPL) and is hosted at https://github.com/ncssar/gpsio. Contributions are welcome; two high priority items are Linux installation support and integration with non-Garmin GPSs (either through auto-detection or a user-selectable GPS type dropdown). Testing with additional GPS units is also valuable; send bug reports to info@caltopo.com.
