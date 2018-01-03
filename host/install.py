from __future__ import print_function
# 1. locate GPSBabel install location
# 2. determine host install location
# 3. copy host files into location
# -- customizing config.py along the way
# 4. copy nmh-manifest.json into location
# -- customizing wrapper.bat / wrapper.py location along the way
# 5. automatically prompt chrome to install the geoext app

import os
import subprocess
import sys

DEFAULT_HOST_LOCATION = {
    'win32': os.path.join(os.path.expanduser('~'), 'gpsio'),
    'darwin': os.path.join(os.path.expanduser('~'), 'Library/com.caltopo.gpsio'),
    'linux': '/opt/gpsio'
}

DEFAULT_GPSBABEL_DIR = {
    'win32': 'GPSBabel',
    'darwin': 'GPSBabelFE.app'
}

DEFAULT_GPSBABEL_NAME = {
    'win32': 'gpsbabel.exe',
    'darwin': 'contents/MacOS/gpsbabel'
}

MANIFEST_INSTALL_LOCATION_CHROME = {
    'win32': 'HOST_LOCATION\\chrome-manifest.json',
    'darwin': os.path.join(os.path.expanduser('~'), 'Library/Application Support/Google/Chrome/NativeMessagingHosts/com.caltopo.gpsio.json'),
    'linux': '~/.config/google-chrome/NativeMessagingHosts/com.caltopo.gpsio.json'
}

MANIFEST_INSTALL_LOCATION_FIREFOX = {
    'win32': 'HOST_LOCATION\\firefox-manifest.json',
    'darwin': os.path.join(os.path.expanduser('~'), 'Library/Application Support/Mozilla/NativeMessagingHosts/com.caltopo.gpsio.json'),
    'linux': '~/.mozilla/native-messaging-hosts/com.caltopo.gpsio.json'
}

def find_gpsbabel():
    print("Looking for a GPSBabel install.  This may take a minute . . .\n")
    items=os.walk(os.path.normpath('/'))
    matches = []
    for item in items:
        if item[0].endswith(DEFAULT_GPSBABEL_DIR[sys.platform]) and os.path.isfile(os.path.join(item[0], DEFAULT_GPSBABEL_NAME[sys.platform])):
            matches.append(os.path.join(item[0], DEFAULT_GPSBABEL_NAME[sys.platform]))

    print("Please identify your GPSBabel install location:")
    if len(matches) == 0:
        print("GPSBabel not found, you may need to install it.")
        print("enter a custom location: ",end='')
        sys.stdout.flush()
    else:
        for i in range(0, len(matches)):
            print("[ " + str(i) + " ] " + matches[i])
        print("")
        print("enter a number or a custom location: ",end='')
        sys.stdout.flush()
    s=sys.stdin.readline().rstrip()
    try:
        i=int(s)
        return matches[i]
    except:
        return s

def get_install_location():
    default = DEFAULT_HOST_LOCATION[sys.platform]
    print("Where would you like to install GPS IO? [enter for default location of " + default + "]? ",end='')
    sys.stdout.flush()
    s=sys.stdin.readline().rstrip()
    if len(s) == 0:
        return default
    return s

def install_host(host_location):
    config_text = """
debug=False
gpsbabel_exe="GPSBABEL_LOCATION"
chunk_size=100000
""".replace("GPSBABEL_LOCATION", gpsbabel_location)

    try:
        os.makedirs(host_location)
    except:
        pass
    if sys.platform == 'win32': # would prefer not to shell out but shutil will not preserve metadata
        subprocess.call("copy \"wrapper.py\" \"" + host_location + "\"", shell=True)
        subprocess.call("copy \"wrapper.bat\" \"" + host_location + "\"", shell=True)
    else:
        subprocess.call(["cp", "wrapper.py", host_location])

    with open(os.path.join(host_location, 'config.py'), 'w') as file:
        file.write(config_text)

def install_manifest(host_location):
    wrapper_path = host_location
    if sys.platform == 'win32':
        wrapper_path = wrapper_path + "\\wrapper.bat"
    else:
        wrapper_path = wrapper_path + "/wrapper.py"

    manifest_location_chrome = MANIFEST_INSTALL_LOCATION_CHROME[sys.platform].replace('HOST_LOCATION', host_location)
    nmh_manifest_chrome = '{"name": "com.caltopo.gpsio","description": "GPS IO","path": "%s","type": "stdio","allowed_origins": ["chrome-extension://afgcejeehpnhafgikkimogllebbgegck/","chrome-extension://hoecjlpnaeogdncffnambjemmfcajmcc/"]}'
    print("placing chrome manifest file in", manifest_location_chrome)
    try:
        os.makedirs(os.path.dirname(manifest_location_chrome))
    except:
        pass
    with open(manifest_location_chrome, "w") as file:
        file.write(nmh_manifest_chrome % wrapper_path.replace("\\", "\\\\"))

    manifest_location_firefox = MANIFEST_INSTALL_LOCATION_FIREFOX[sys.platform].replace('HOST_LOCATION', host_location)
    nmh_manifest_firefox = '{"name": "com.caltopo.gpsio","description": "GPS IO","path": "%s","type": "stdio","allowed_extensions": ["gpsio@caltopo.com"]}'
    print("placing firefox manifest file in", manifest_location_firefox)
    try:
        os.makedirs(os.path.dirname(manifest_location_firefox))
    except:
        pass
    with open(manifest_location_firefox, "w") as file:
        file.write(nmh_manifest_firefox % wrapper_path.replace("\\", "\\\\"))

    if sys.platform == 'win32':
        subprocess.call(["REG", "ADD", "HKCU\\Software\\Google\\Chrome\\NativeMessagingHosts\\com.caltopo.gpsio", "/ve", "/t", "REG_SZ", "/d", manifest_location_chrome, "/f"])
        subprocess.call(["REG", "ADD", "HKCU\\SOFTWARE\\Mozilla\\NativeMessagingHosts\\com.caltopo.gpsio", "/ve", "/t", "REG_SZ", "/d", manifest_location_firefox, "/f"])

print("GPSIO host installer v1")
gpsbabel_location = find_gpsbabel()
host_location = get_install_location()

print("installing native messaging host at", host_location)
install_host(host_location)

install_manifest(host_location)

print("\n\npress enter to exit:",end='')
sys.stdout.flush()
sys.stdin.readline()