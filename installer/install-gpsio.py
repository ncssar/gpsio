
# TODO: native host install logic: if/when/how to overwrite host dir file(s) on new install
#     (make sure to not clobber edited files, or at least back them up)
# TODO: check for issues due to the fact that this script is run as admin
# TODO: delete extension-trigger-registry-keys on first error (key exists but extension is not installed)
# TODO: automatically pin the extension in chrome, or document the fact that you need to do it by hand
# TODO: Mac
# TODO: Linux

# TODO: investigate sending gpsio-host.py updates via new extension versions



# install-gpsio.py - attempt to install as many parts of the GPSIO tool
#  as possible from a python script.  Since linux and mac will require
#  a python script to do the installation anyway, it's best to centralize
#  all of the code here.  Make it callable step-by-step from the command
#  line, to enable a NSIS graphical interface that shows step-by-step progress.

# SYNTAX:
# python install-gpsio.py [OPTION]... [STAGE]...

# EXAMPLE:
# python install-gpsio.py -min 1a 1b 1c 2
#  this will produce minimal output and will run stages 1a, 1b, 1c, and 2 before exiting

# OPTIONS:
# -min - produce minimal output - for use with GUI installer (NSIS for Windows)

# stages:
# 1a. attempt to install Chrome extension
# 1b. attempt to install Firefox extension
# 1c. attempt to install Edge extension
# 2. attempt to install GPSBabel
# 3. attempt to install Garmin USB drivers (Windows only)
# 4. attempt to install native host

import argparse
import os
import subprocess
import sys
import shutil
import glob

win32=sys.platform=='win32'
darwin=sys.platform=='darwin'
linux=sys.platform=='linux'

# For python 3.8 or later on Windows, this line is required before 'import oschmod',
#  to avoid 'ImportError: DLL load failed while importing win32security: ...'
# see https://stackoverflow.com/a/67437837/3577105
#  specifying a relative path fails with 'the parameter is incorrect'

pwd=os.path.dirname(os.path.realpath(__file__))
if win32:
    os.add_dll_directory(os.path.join(pwd,'host','dist','pywin32_system32'))

import oschmod

parser=argparse.ArgumentParser()
parser.add_argument('-min',action='store_true')
parser.add_argument('stages',type=str,nargs='+')
args=parser.parse_args()

gpsbabel_exe=False
ltxt=''

# platform independent constants
INSTALL_TMP=pwd # normally, the current directory is the unzipped tmp directory
CHROME_EXTENSION_ID='cbpembjdolhcjepjgdkcflipfojbjall' # published on Chrome Web Store
FIREFOX_EXTENSION_ID='{5da30c55-01fd-4045-a0d2-41c47ebc8b83}' # published on AMO (addons.mozilla.org)
EDGE_EXTENSION_ID='gnonahdiojppiacfbalpgjddpkfepihk' # published on Edge Add-ons
CHROME_UPDATE_URL='https://clients2.google.com/service/update2/crx'
EDGE_UPDATE_URL='https://edge.microsoft.com/extensionwebstorebase/v1/crx'
EXTENSION_HANDLE='com.caltopo.gpsio'

# platform dependent constants
if win32:
    # directory constants
    PF='C:\\Program Files'
    PF86=PF+' (x86)'
    HOST_DIR=PF86+'\\GPSIO'
    CHROME_EXTENSIONS_FOLDER=os.getenv('LOCALAPPDATA')+'\\Google\\Chrome\\User Data\\Default\\Extensions'
    FIREFOX_PROFILES_FOLDER=os.getenv('APPDATA')+'\\Mozilla\\Firefox\\Profiles'
    EDGE_EXTENSIONS_FOLDER=os.getenv('LOCALAPPDATA')+'\\Microsoft\\Edge\\User Data\\Default\\Extensions'

    # registry entry constants
    CHROME_REGISTRY_BASE_KEY='SOFTWARE\\WOW6432Node\\Google\\Chrome\\Extensions'
    CHROME_REGISTRY_FULL_KEY=CHROME_REGISTRY_BASE_KEY+'\\'+CHROME_EXTENSION_ID
    EDGE_REGISTRY_BASE_KEY='SOFTWARE\\WOW6432Node\\Microsoft\\Edge\\Extensions'
    EDGE_REGISTRY_FULL_KEY=EDGE_REGISTRY_BASE_KEY+'\\'+EDGE_EXTENSION_ID
    UNINSTALL_ROOT='SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
    UNINSTALL_WOW_ROOT='SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
    CHROME_NMH_KEY='Software\\Google\\Chrome\\NativeMessagingHosts\\'+EXTENSION_HANDLE
    FIREFOX_NMH_KEY='Software\\Mozilla\\NativeMessagingHosts\\'+EXTENSION_HANDLE
    EDGE_NMH_KEY='Software\\Microsoft\\Edge\\NativeMessagingHosts\\'+EXTENSION_HANDLE
elif darwin:
    pass
elif linux:
    pass
else:
    print('unknown platform '+str(sys.platform))
    sys.exit(1)


def findRegKeyWithEntry(keyName,entryName,entryValue):
    if 'WOW64' in keyName:
        flags=winreg.KEY_READ
    else:
        flags=winreg.KEY_WOW64_64KEY|winreg.KEY_READ
    key=winreg.OpenKey(HKLM,keyName,access=flags)
    more=True
    i=0
    while more:
        try:
            subkeyName=winreg.EnumKey(key,i)
        except OSError:
            more=False
        else:
            i=i+1
            subkey=winreg.OpenKey(key,subkeyName)
            try:
                val=winreg.QueryValueEx(subkey,entryName)
            except:
                pass
            else:
                if val[0]==entryValue:
                    return subkeyName
    return None
                    

# platform dependent common code
if win32:
    import winreg
    HKLM=winreg.HKEY_LOCAL_MACHINE
    HKCU=winreg.HKEY_CURRENT_USER


# 1a. attempt to install Chrome extension
def stage_1a():
    global ltxt
    #  is the extension already installed?
    if os.path.isdir(os.path.join(CHROME_EXTENSIONS_FOLDER,CHROME_EXTENSION_ID)):
        print('  1a. Chrome Extension --> DONE')
        return
    else:
        if win32: # add registry entry if needed
            flags=winreg.KEY_ALL_ACCESS
            if 'WOW64' in CHROME_REGISTRY_BASE_KEY:
                flags=winreg.KEY_ALL_ACCESS|winreg.KEY_WOW64_64KEY
            try:
                key=winreg.CreateKeyEx(HKLM,CHROME_REGISTRY_FULL_KEY,access=flags)
            except PermissionError:
                print('Permission error: Chrome key cannot be opened with KEY_ALL_ACCESS permission.  This script must be run as administrator.')
                return
            needToWrite=False
            try:
                val=winreg.QueryValueEx(key,'update_url')
            except PermissionError:
                print('Permission error: Chrome key value cannot be queried')
                return
            except: # value does not exist
                needToWrite=True
            else:
                if val[0]==CHROME_UPDATE_URL: # key exists but extension was not installed; maybe on blocklist
                    print('  1a. Chrome Extension --> FAILED')
                    ltxt+='\n\nCHROME EXTENSION - INSTALLATION FAILED\nYou will need to add the extension to Chrome by hand (i.e. from Chrome).  You can search for \'gpsio\' at the Chrome Web Store.  The direct link is in the documentation at github.com/ncssar/gpsio.'
                    return
                else:
                    needToWrite=True
            if needToWrite:
                winreg.SetValueEx(key,'update_url',0,winreg.REG_SZ,CHROME_UPDATE_URL)
                print('  1a. Chrome Extension --> DONE')
                ltxt+='\n\nCHROME EXTENSION installation has been triggered; on or before the next time you start Chrome, it should prompt you to enable the gpsio extension.  Make sure to enable the extension.'
            winreg.CloseKey(key)

# 1b. attempt to install Firefox extension
def stage_1b():
    global ltxt
    #  is the extension already installed?
    import glob
    firefox_profile_name=glob.glob(os.path.join(FIREFOX_PROFILES_FOLDER,'*.default'))[0]
    firefox_extensions_folder=os.path.join(FIREFOX_PROFILES_FOLDER,firefox_profile_name,'extensions')
    if os.path.isfile(os.path.join(firefox_extensions_folder,FIREFOX_EXTENSION_ID+'.xpi')):
        print('  1b. Firefox Extension --> DONE')
    else:
        xpi=os.path.join(INSTALL_TMP,FIREFOX_EXTENSION_ID+'.xpi')
        if os.path.isfile(xpi):
            shutil.copyfile(xpi,firefox_extensions_folder)
            print('  1b. Firefox Extension --> DONE')
            ltxt+='\n\nFIREFOX EXTENSION installation has been triggered; on or before the next time you start Firefox, it may prompt you to enable the gpsio extension.  Make sure to enable the extension.'
        else:
            print('  1b. Firefox Extension --> FAILED')
            ltxt+='\n\nFIREFOX EXTENSION installation failed; it appears the required .xpi file was not extracted with the GPSIO installer.  Please contact the developer.'


# 1c. attempt to install Edge extension
def stage_1c():
    global ltxt
    #  is the extension already installed?
    if os.path.isdir(os.path.join(EDGE_EXTENSIONS_FOLDER,EDGE_EXTENSION_ID)):
        print('  1c. Edge Extension --> DONE')
        return
    else:
        if win32: # add registry entry if needed
            flags=winreg.KEY_ALL_ACCESS
            if 'WOW64' in CHROME_REGISTRY_BASE_KEY:
                flags=winreg.KEY_ALL_ACCESS|winreg.KEY_WOW64_64KEY
            try:
                key=winreg.CreateKeyEx(HKLM,EDGE_REGISTRY_FULL_KEY,access=flags)
            except PermissionError:
                print('Permission error: Edge key cannot be opened with KEY_ALL_ACCESS permission.  This script must be run as administrator.')
                return
            except Exception as e:
                print(e)
                return
            needToWrite=False
            try:
                val=winreg.QueryValueEx(key,'update_url')
            except PermissionError:
                print('Permission error: Edge key value cannot be queried')
                return
            except: # value does not exist
                needToWrite=True
            else:
                if val[0]==EDGE_UPDATE_URL: # key exists but extension was not installed; maybe on blocklist
                    print('  1c. Edge Extension --> FAILED')
                    ltxt+='\n\nEDGE EXTENSION - INSTALLATION FAILED\nYou will need to add the extension to Edge by hand (i.e. from Edge).  You can search for \'gpsio\' at microsoftedge.microsoft.com.  The direct link is in the documentation at github.com/ncssar/gpsio.'
                    return
                else:
                    needToWrite=True
            if needToWrite:
                winreg.SetValueEx(key,'update_url',0,winreg.REG_SZ,EDGE_UPDATE_URL)
                print('  1c. Edge Extension --> DONE')
                ltxt+="\n\nEDGE EXTENSION installation has been triggered; on or before the next time you start Edge, it should prompt you to enable the gpsio extension.  Make sure to enable the extension."
            winreg.CloseKey(key)

# 2. attempt to install GPSBabel
def stage_2():
    global ltxt
    if win32:
        subkeyName=findRegKeyWithEntry(UNINSTALL_WOW_ROOT,'DisplayName','GPSBabel 1.7.0')
        if subkeyName: # key found: read the install path value and make sure gpsbabel.exe is there
            # print('matching key: '+str(subkeyName))
            keyName=UNINSTALL_WOW_ROOT+'\\'+subkeyName
            # print('full key name: '+keyName)
            key=winreg.OpenKey(HKLM,keyName)
            loc=winreg.QueryValueEx(key,'InstallLocation')[0]
            global gpsbabel_exe
            gpsbabel_exe=os.path.join(loc,'gpsbabel.exe')
            if os.path.isfile(gpsbabel_exe):
                print('2. GPSBabel --> DONE')
            else:
                print('2. GPSBabel --> FAILED')
                ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe existing installation could not be confirmed.  Please uninstall then re-install GPSBabel using the online installer from gpsbabel.org.'
        else:
            print('2. GPSBabel --> installing...')
            subprocess.run([os.path.join(INSTALL_TMP,'GPSBabel-1.7.0-Setup.exe')])
            print('2. GPSBabel --> installer completed; verifying...')
            # check again: duplicated / repeated code from above - not a big problem
            subkeyName=findRegKeyWithEntry(UNINSTALL_WOW_ROOT,'DisplayName','GPSBabel 1.7.0')
            if subkeyName: # key found: read the install path value and make sure gpsbabel.exe is there
                # print('matching key: '+str(subkeyName))
                keyName=UNINSTALL_WOW_ROOT+'\\'+subkeyName
                # print('full key name: '+keyName)
                key=winreg.OpenKey(HKLM,keyName)
                loc=winreg.QueryValueEx(key,'InstallLocation')[0]
                gpsbabel_exe=os.path.join(loc,'gpsbabel.exe')
                if os.path.isfile(gpsbabel_exe):
                    print('2. GPSBabel --> DONE')
                else:
                    print('2. GPSBabel --> FAILED')
                    ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe fresh installation could not be confirmed.  The registry key was found, but the executable was not.  Please uninstall then re-install GPSBabel using the online installer from gpsbabel.org.'
            else:
                print('2. GPSBabel --> FAILED')
                ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe fresh installation could not be confirmed.  The registry key was not found.  Please uninstall then re-install GPSBabel using the online installer from gpsbabel.org.'


# 3. attempt to install Garmin USB drivers (Windows only)
def stage_3():
    global ltxt
    subkeyName=findRegKeyWithEntry(UNINSTALL_ROOT,'DisplayName','Garmin USB Drivers')
    if subkeyName:
        print('3. Garmin USB Drivers --> DONE')
    else:
        d=os.path.join(INSTALL_TMP,'USBDrivers_2312.exe')
        if os.path.isfile(d):
            subprocess.run([d])
            print('3. Garmin USB Drivers --> DONE')
        else:
            print('3. Garmin USB Drivers --> FAILED')
            ltxt+='\n\nGARMIN USB DRIVERS INSTALLATION FAILED - the Garmin USB Driver installation program was not found in the GPSIO installation temporary directory.'


# 4. attempt to install native host
def stage_4():
    global ltxt
    if not os.path.isdir(HOST_DIR):
        if os.path.isdir(INSTALL_TMP):
            # copy files into place
            shutil.copytree(os.path.join(INSTALL_TMP,'host'),HOST_DIR)
        else:
            print('4. Native Host --> FAILED')
            ltxt+='\n\nNATIVE HOST INSTALLATION FAILED - the temporary installation directory, which should contain the necessary extracted files, does not exist.'
            return

    # add edit permissions for all to gpsio-host.* in case the user needs to modify them
    for f in glob.glob(HOST_DIR+'\\gpsio-host.*'):
        oschmod.set_mode(f,'a+w')

    # create the host manifest files for each extension
    HOST_DIR_DOUBLE_SLASH=HOST_DIR.replace('\\','\\\\')
    with open(os.path.join(HOST_DIR,'chrome-manifest.json'),'w') as f:
        f.write('{\n  "name": "'+EXTENSION_HANDLE+'",\n  "description": "GPS IO",\n  "path": "'+HOST_DIR_DOUBLE_SLASH+'/gpsio-host.bat",\n  "type": "stdio",\n  "allowed_origins": [\n    "chrome-extension://'+CHROME_EXTENSION_ID+'/"\n  ]\n}')
    with open(os.path.join(HOST_DIR,'firefox-manifest.json'),'w') as f:
        f.write('{\n  "name": "'+EXTENSION_HANDLE+'",\n  "description": "GPS IO",\n  "path": "'+HOST_DIR_DOUBLE_SLASH+'/gpsio-host.bat",\n  "type": "stdio",\n  "allowed_extensions": [\n    '+FIREFOX_EXTENSION_ID+'"\n  ]\n}')
    with open(os.path.join(HOST_DIR,'edge-manifest.json'),'w') as f:
        f.write('{\n  "name": "'+EXTENSION_HANDLE+'",\n  "description": "GPS IO",\n  "path": "'+HOST_DIR_DOUBLE_SLASH+'/gpsio-host.bat",\n  "type": "stdio",\n  "allowed_origins": [\n    "chrome-extension://'+EDGE_EXTENSION_ID+'/"\n  ]\n}')

    # write registry entries for host manifest file locations
    winreg.SetValueEx(winreg.CreateKey(HKCU,CHROME_NMH_KEY),'',0,winreg.REG_SZ,os.path.join(HOST_DIR,'chrome-manifest.json'))
    winreg.SetValueEx(winreg.CreateKey(HKCU,FIREFOX_NMH_KEY),'',0,winreg.REG_SZ,os.path.join(HOST_DIR,'firefox-manifest.json'))
    winreg.SetValueEx(winreg.CreateKey(HKCU,EDGE_NMH_KEY),'',0,winreg.REG_SZ,os.path.join(HOST_DIR,'edge-manifest.json'))
    
    # edit gpsio-host.ini with confirmed gpsbabel executable path
    if gpsbabel_exe:
        with open('gpsio-host.ini','r') as f:
            fdata=f.read()
        fdata=fdata.replace('UNDEFINED',gpsbabel_exe)
        with open('gpsio-host.ini','w') as f:
            f.write(fdata)
        
    print('4. Native Host --> DONE')

# 5. cleanup of items that python is aware of
def stage_5():
    if win32:
        shutil.rmtree(os.path.join(HOST_DIR,'dist','win32'),ignore_errors=True)
        shutil.rmtree(os.path.join(HOST_DIR,'dist','pywin32_system32'),ignore_errors=True)
        shutil.rmtree(os.path.join(HOST_DIR,'dist','oschmod'),ignore_errors=True)

####################################################################
# top level code: run the requested functions, in alphabetical order
####################################################################
args.stages.sort()                
for stage in args.stages:
    funcName='stage_'+stage
    globals()[funcName]()

if ltxt!='':
    with open(os.path.join(INSTALL_TMP,'install-notices.txt'),'a') as f:
        f.write(ltxt)

