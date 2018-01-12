from __future__ import print_function
import json
import os
import shutil
import subprocess
import zipfile

print("building host")
try:
    os.remove("build/gpsio-installer.zip")
except:
    pass
  
zipf=zipfile.ZipFile("build/gpsio-installer.zip", "w", zipfile.ZIP_DEFLATED)
host_filenames = ("install.py","wrapper.py","wrapper.bat")
for filename in host_filenames:
    zipf.write("host/" + filename, "gpsio-installer/" + filename)
zipf.close()

extension_filenames = ("background.js","content_script.js","gps.png","popup.html","popup.js","popup.css")
def create_extension_zip(name, manifest):
    zipf=zipfile.ZipFile("build/" + name + ".zip", "w", zipfile.ZIP_DEFLATED)
    for filename in extension_filenames:
        zipf.write("extension/" + filename, filename)
    zipf.writestr("manifest.json", json.dumps(manifest))
    zipf.close()
  
manifest=json.loads(open('extension/manifest.json').read())
print("building extension zipfiles")
try:
    os.remove("build/firefox-1.zip")
    os.remove("build/firefox-2.zip")
    os.remove("build/chrome-1.zip")
    os.remove("build/chrome-2.zip")
except:
    pass


manifest.pop('key', None)
create_extension_zip("firefox-1", manifest)

manifest['applications']['gecko']['id']='gpsio2@caltopo.com'
manifest['content_scripts'][0]['matches'] = ["https://caltopo.com/*","http://caltopo.com/*","https://sartopo.com/*","http://sartopo.com/*","http://localhost:8080/*"]
create_extension_zip("firefox-2", manifest)

manifest.pop('applications', None)
create_extension_zip("chrome-2", manifest)
manifest['content_scripts'][0]['matches'] = ["https://*/*","http://*/*"]
create_extension_zip("chrome-1", manifest)
