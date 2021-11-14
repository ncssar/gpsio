del gpsio-chrome-extension.zip
del gpsio-firefox-extension.zip
del gpsio-edge-extension.zip
tar -acvf gpsio-chrome-extension.zip -C common *.* -C ..\chrome *.*
tar -acvf gpsio-firefox-extension.zip -C common *.* -C ..\firefox *.*
tar -acvf gpsio-edge-extension.zip -C common *.* -C ..\edge *.*

