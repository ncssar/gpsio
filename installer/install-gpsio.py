#!/usr/bin/python3

# TODO: Mac
# TODO: Linux

# install-gpsio.py - attempt to install as many parts of the GPSIO tool
#  as possible from a python script.  Since linux and mac will require
#  a python script to do the installation anyway, it's best to centralize
#  all of the code here.  Make it callable step-by-step from the command
#  line, to enable a graphical interface that shows step-by-step progress.
#
# for Windows, this script is called once per stage by the Nullsoft (NSIS) installer.

# SYNTAX:
# python install-gpsio.py [STAGE]...

# EXAMPLE:
# python install-gpsio.py 1a 1b 1c 2
#  this will run stages 1a, 1b, 1c, and 2 before exiting

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
import time
from datetime import datetime
import filecmp
import stat

win32=sys.platform=='win32'
darwin=sys.platform=='darwin'
linux=sys.platform=='linux'

def log(t):
    print(t)
    if darwin:
        with open(os.path.join(HOST_DIR,'install-log.txt'),'a') as f:
            f.write(t+'\n')

if darwin|linux:
    if not os.geteuid() == 0:
        sys.exit('ERROR: gpsio-init.py must be run as root.')

# For python 3.8 or later on Windows, this line is required before 'import oschmod',
#  to avoid 'ImportError: DLL load failed while importing win32security: ...'
# see https://stackoverflow.com/a/67437837/3577105
#  specifying a relative path fails with 'the parameter is incorrect'

# don't import oschmod for darwin/linux, since it isn't built in - os.chmod should work fine
pwd=os.path.dirname(os.path.realpath(__file__))
if win32:
    os.add_dll_directory(os.path.join(pwd,'host','dist','pywin32_system32'))
    import oschmod

# for Windows, this is called from NSIS, and there will be one argument: stage to run
# for Mac, this is called from installer, and the arguments will be predetermined by pkgbuild
if win32:
    parser=argparse.ArgumentParser()
    parser.add_argument('stages',type=str,nargs='+')
    args=parser.parse_args()
elif darwin:
    stages=['1a','1b','1c','2','3','4']

gpsbabel_exe=False
ltxt=''

# platform independent constants
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
    INSTALL_TMP=pwd # normally, the current directory is the unzipped tmp directory
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

    HOST_MANIFEST_FILE={
        'chrome':os.path.join(HOST_DIR,'chrome-manifest.json'),
        'firefox':os.path.join(HOST_DIR,'firefox-manifest.json'),
        'edge':os.path.join(HOST_DIR,'edge-manifest.json')}

elif darwin:
    # # when called from installer (from package generated with pkgbuild), argv[2] is the installer target dir
    # if len(sys.argv)>2 and os.path.isdir(sys.argv[2]):
    #     HOST_DIR=sys.argv[2]
    # else:
    #     HOST_DIR='/Library/'+EXTENSION_HANDLE
    HOST_DIR='/Library/gpsio'
    INSTALL_TMP=HOST_DIR
    CHROME_EXTENSIONS_FOLDER='~/Library/Application Support/Google/Chrome/Default/Extensions'
    EDGE_EXTENSIONS_FOLDER='~/Library/Application Support/Microsoft/Edges/Default/Extensions'
    CHROME_INSTALL_JSON='/Library/Application Support/Google/Chrome/External Extensions/'+CHROME_EXTENSION_ID+'.json'
    EDGE_INSTALL_JSON='/Library/Application Support/Microsoft/Edge/External Extensions/'+EDGE_EXTENSION_ID+'.json'
    HOST_MANIFEST_FILE={
        'chrome':'/Library/Google/Chrome/NativeMessagingHosts/com.caltopo.gpsio.json',
        'firefox':'/Library/Application Support/Mozilla/NativeMessagingHosts/com.caltopo.gpsio.json',
        'edge':'/Library/Microsoft/Edge/NativeMessagingHosts/com.caltopo.gpsio.json'}

elif linux:
    HOST_DIR='/dev/null'
    HOST_MANIFEST_FILE={
        'chrome':'/etc/opt/chrome/native-messaging-hosts/com.caltopo.gpsio.json',
        'firefox':'/usr/lib64/mozilla/native-messaging-hosts/com.caltopo.gpsio.json',
        'edge':'/etc/opt/edge/native-messaging-hosts/com.caltopo.gpsio.json'}

else:
    log('unknown platform '+str(sys.platform))
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

def getDarwinApps():    
    return str(subprocess.run(['mdfind',"kMDItemKind == 'Application'"],capture_output=True).stdout,'utf-8').split('\n')
             
# findGPSBabel - returns a two-element list: [installed,exe]
#    installed - boolean indicating whether it was apparently previously installed
#    exe - full verified path to the executable, or None if not found
def findGPSBabel():
    if win32:
        subkeyName=findRegKeyWithEntry(UNINSTALL_WOW_ROOT,'DisplayName','GPSBabel 1.7.0')
        if subkeyName: # key found: read the install path value and make sure gpsbabel.exe is there
            keyName=UNINSTALL_WOW_ROOT+'\\'+subkeyName
            key=winreg.OpenKey(HKLM,keyName)
            loc=winreg.QueryValueEx(key,'InstallLocation')[0]
            gpsbabel_exe=os.path.join(loc,'gpsbabel.exe')
            if os.path.isfile(gpsbabel_exe):
                return [True,gpsbabel_exe]
            else:
                return [True,None] # apparently installed, but referenced executable not found
        else:
            return [False,None] # apparently not installed
    elif darwin:
        apps=getDarwinApps()
        gpsbabel_appdir=None
        gpsbabel_appentries=[x for x in apps if 'GPSBabel' in x]
        if gpsbabel_appentries:
            gpsbabel_appdir=gpsbabel_appentries[0]
        if gpsbabel_appdir:
            gpsbabel_exe=os.path.join(gpsbabel_appdir,'Contents','MacOS','gpsbabel')
            if os.path.isfile(gpsbabel_exe):
                return [True,gpsbabel_exe]
            else:
                return [True,None] # apparently installed, but referenced executable not found
        else:
            return [False,None] # apparently not installed

# platform dependent top-level code
if win32:
    import winreg
    HKLM=winreg.HKEY_LOCAL_MACHINE
    HKCU=winreg.HKEY_CURRENT_USER


# 1. attempt to install browser extensions
# the chrome and edge docs imply that this is an 'externally installed' extension, i.e.
#  installed by copying a file from somewhere other than the Chrome Web Store or Edge Add-ons.
#  That's not the case.  These methods - registry for Windows, or json for mac and linux -
#  signal the browser to download the extension from the official web store.  If currently offline,
#  the browser will download and add the extension the next time it is online.
# https://developer.chrome.com/docs/extensions/mv3/external_extensions/
#  (for firefox, just copy the .xpi file into place)
# https://docs.microsoft.com/en-us/microsoft-edge/extensions-chromium/developer-guide/alternate-distribution-options

# 1a. attempt to install Chrome extension
def stage_1a():
    global ltxt
    #  is the extension already installed?
    if os.path.isdir(os.path.join(CHROME_EXTENSIONS_FOLDER,CHROME_EXTENSION_ID)):
        log('  1a. Chrome Extension : already installed')
        return
    else:
        if win32: # add registry entry if needed
            flags=winreg.KEY_ALL_ACCESS
            if 'WOW64' in CHROME_REGISTRY_BASE_KEY:
                flags=winreg.KEY_ALL_ACCESS|winreg.KEY_WOW64_64KEY
            try:
                key=winreg.CreateKeyEx(HKLM,CHROME_REGISTRY_FULL_KEY,access=flags)
            except PermissionError:
                log('Permission error: Chrome key cannot be opened with KEY_ALL_ACCESS permission.  This script must be run as administrator.')
                return
            needToWrite=False
            try:
                val=winreg.QueryValueEx(key,'update_url')
            except PermissionError:
                log('Permission error: Chrome key value cannot be queried')
                return
            except: # value does not exist
                needToWrite=True
            else:
                if val[0]==CHROME_UPDATE_URL:
                    # key exists with correct value, but extension directory was not found;
                    #  this does not mean the attempt failed;
                    #  attempting to verify by checking the directory again is not reliable:
                    #  - maybe blocklisted
                    #  - maybe browser is not installed
                    #  - maybe browser is installed but not currently running
                    #  but we can try one more time by deleting and re-adding update_url
                    winreg.DeleteValue(key,'update_url')
                    time.sleep(1)
                    needToWrite=True
                    # log('  1a. Chrome Extension : FAILED')
                    # ltxt+='\n\nCHROME EXTENSION - INSTALLATION FAILED\nIf you use Chrome, you will need to add the extension to Chrome by hand (i.e. from Chrome).  You can search for \'gpsio\' at the Chrome Web Store.  The direct link is in the documentation at github.com/ncssar/gpsio.'
                    # return
                else:
                    needToWrite=True
            if needToWrite:
                winreg.SetValueEx(key,'update_url',0,winreg.REG_SZ,CHROME_UPDATE_URL)
                log('  1a. Chrome Extension : installation attempted')
                # ltxt+='\n\nCHROME EXTENSION installation has been triggered; on or before the next time you start Chrome, you to enable the gpsio extension.  Make sure to enable the extension.'
            winreg.CloseKey(key)
        elif darwin:
            # add json file - this doesn't take effect til Chrome restart, and it is silent and not enabled by default,
            #  so the user will probably add the extension by hand instead; but we may as well try
            os.makedirs(os.path.dirname(CHROME_INSTALL_JSON),exist_ok=True)
            with open(CHROME_INSTALL_JSON,'w') as f:
                f.write('{\n  "external_update_url":"'+CHROME_UPDATE_URL+'"\n}')
                log('  1a. Chrome Extension : installation attempted')


# 1b. attempt to install Firefox extension
def stage_1b():
    global ltxt
    xpiSource=os.path.join(INSTALL_TMP,FIREFOX_EXTENSION_ID+'.xpi')
    if not os.path.isfile(xpiSource):
        log('  1b. Firefox Extension : FAILED')
        ltxt+='\n\nFIREFOX EXTENSION installation failed; it appears the required .xpi file was not extracted with the GPSIO installer.  Please contact the developer.'
        return
    # since the current profile can't be determined from code, just install it to all profiles
    if os.path.isdir(FIREFOX_PROFILES_FOLDER): # won't exist if Firefox is not installed
        installedCount=0
        firefox_profile_names=os.listdir(FIREFOX_PROFILES_FOLDER)
        for firefox_profile_name in firefox_profile_names:
            firefox_extensions_folder=os.path.join(FIREFOX_PROFILES_FOLDER,firefox_profile_name,'extensions')
            # if no other extensions have been installed, prevent creation of a file named 'Extensions'
            os.makedirs(firefox_extensions_folder,exist_ok=True)
            xpiTarget=os.path.join(firefox_extensions_folder,FIREFOX_EXTENSION_ID+'.xpi')
            if not os.path.isfile(xpiTarget):
                installedCount+=1
                shutil.copyfile(xpiSource,xpiTarget)
        if installedCount==0:
            log('  1b. Firefox Extension: already installed for all profiles')
        else:
            suffix=''
            if installedCount>1:
                suffix='s'
            log('  1b. Firefox Extension: installed for '+str(installedCount)+' profile'+suffix)
            ltxt+='\n\nFIREFOX EXTENSION installation has been triggered for '+str(installedCount)+' profile'+suffix+'; on or before the next time you start Firefox, it may prompt you to enable the gpsio extension.  Make sure to enable the extension.'
    else:
        log('  1b. Firefox Extension : skipped')
        ltxt+='\n\nFIREFOX EXTENSION installation was skipped; it appears you do not have Firefox installed, since its AppData folder does not exist.  You can re-run this installer to try again later, or add the extension by hand from Firefox.'

# 1c. attempt to install Edge extension
def stage_1c():
    global ltxt
    #  is the extension already installed?
    if os.path.isdir(os.path.join(EDGE_EXTENSIONS_FOLDER,EDGE_EXTENSION_ID)):
        log('  1c. Edge Extension : already installed')
        return
    else:
        if win32: # add registry entry if needed
            flags=winreg.KEY_ALL_ACCESS
            if 'WOW64' in CHROME_REGISTRY_BASE_KEY:
                flags=winreg.KEY_ALL_ACCESS|winreg.KEY_WOW64_64KEY
            try:
                key=winreg.CreateKeyEx(HKLM,EDGE_REGISTRY_FULL_KEY,access=flags)
            except PermissionError:
                log('Permission error: Edge key cannot be opened with KEY_ALL_ACCESS permission.  This script must be run as administrator.')
                return
            except Exception as e:
                log(e)
                return
            needToWrite=False
            try:
                val=winreg.QueryValueEx(key,'update_url')
            except PermissionError:
                log('Permission error: Edge key value cannot be queried')
                return
            except: # value does not exist
                needToWrite=True
            else:
                if val[0]==EDGE_UPDATE_URL:
                    # key exists with correct value, but extension directory was not found;
                    #  this does not mean the attempt failed;
                    #  attempting to verify by checking the directory again is not reliable:
                    #  - maybe blocklisted
                    #  - maybe browser is not installed
                    #  - maybe browser is installed but not currently running
                    #  but we can try one more time by deleting and re-adding update_url
                    winreg.DeleteValue(key,'update_url')
                    time.sleep(1)
                    needToWrite=True
                else:
                    needToWrite=True
            if needToWrite:
                winreg.SetValueEx(key,'update_url',0,winreg.REG_SZ,EDGE_UPDATE_URL)
                log('  1c. Edge Extension : installation attempted')
                # ltxt+="\n\nEDGE EXTENSION installation has been triggered; on or before the next time you start Edge, it should prompt you to enable the gpsio extension.  Make sure to enable the extension."
            winreg.CloseKey(key)
        elif darwin:
            # add json file - this doesn't take effect til Edge restart, and it is silent and not enabled by default,
            #  so the user will probably add the extension by hand instead; but we may as well try
            os.makedirs(os.path.dirname(EDGE_INSTALL_JSON),exist_ok=True)
            with open(EDGE_INSTALL_JSON,'w') as f:
                f.write('{\n  "external_update_url":"'+EDGE_UPDATE_URL+'"\n}')
                log('  1c. Edge Extension : installation attempted')

# 2. attempt to install GPSBabel
def stage_2():
    global ltxt
    global gpsbabel_exe
    g=findGPSBabel()
    if g[0]: # previously installed
        if g[1]: # executable verified
            gpsbabel_exe=g[1]
            log('2. GPSBabel : previous installation verified')
            return
        else: # apparently previously installed, but executable not found
            log('2. GPSBabel : FAILED')
            ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nA previous installation was detected, but the executable file it refers to could not be found.  Please uninstall GPSBabel, then re-install GPSBabel using the online installer from gpsbabel.org.  You may then need to update the gpsbabel_exe location in gpsio-host.ini in the host folder.'
            return
    else: # not previously installed - install now
        if win32:
            e=os.path.join(INSTALL_TMP,'GPSBabel-1.7.0-Setup.exe')
            if os.path.isfile(e):
                subprocess.run([e])
            else:
                log('2. GPSBabel : FAILED')
                ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe required installer GPSBabel-1.7.0-Setup.exe is not part of the installation bundle.  Please install GPSBabel using the online installer from gpsbabel.org.  You may then need to update the gpsbabel_exe location in gpsio-host.ini in the host folder.'
                return
        elif darwin:
            e='GPSBabel-1.7.0.dmg'
            if os.path.isfile(e):
                subprocess.run(['hdiutil','attach','-mountpoint','./mount','GPSBabel-1.7.0.dmg'])
                try:
                    shutil.copytree('mount/GPSBabelFE.app','/Applications/GPSBabelFE.app')
                except:
                    pass
                subprocess.run(['hdiutil','detach','./mount'])
            else:
                log('2. GPSBabel : FAILED')
                ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe required installer '+e+' is not part of the installation bundle.  Please install GPSBabel using the online installer from gpsbabel.org.  You may then need to update the gpsbabel_exe location in gpsio-host.ini in the host folder.'
                return

    # check again
    time.sleep(3)
    g=findGPSBabel()
    if g[0]: # installed
        if g[1]: # executable verified
            gpsbabel_exe=g[1]
            log('2. GPSBabel : installed and verified')
        else: # installed but executable was not found
            log('2. GPSBabel : FAILED')
            ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe fresh installation could not be confirmed.  The executable file refered to by the fresh installation was not found.  Please uninstall GPSBabel, then re-install GPSBabel using the online installer from gpsbabel.org.  You may then need to update the gpsbabel_exe location in gpsio-host.ini in the host folder.'
    else: # fresh install failed
        log('2. GPSBabel : FAILED')
        ltxt+='\n\nGPSBABEL - INSTALLATION FAILED\nThe fresh installation attempt apparently did not work.  Please install GPSBabel using the online installer from gpsbabel.org.  You may then need to update the gpsbabel_exe location in gpsio-host.ini in the host folder.'          

# 3. attempt to install Garmin USB drivers (Windows only)
def stage_3():
    global ltxt
    if win32:
        subkeyName=findRegKeyWithEntry(UNINSTALL_ROOT,'DisplayName','Garmin USB Drivers')
        if subkeyName:
            log('3. Garmin USB Drivers : already installed')
        else:
            d=os.path.join(INSTALL_TMP,'USBDrivers_2312.exe')
            if os.path.isfile(d):
                subprocess.run([d])
                log('3. Garmin USB Drivers : installed')
            else:
                log('3. Garmin USB Drivers : FAILED')
                ltxt+='\n\nGARMIN USB DRIVERS INSTALLATION FAILED - the Garmin USB Driver installation program was not found in the GPSIO installation temporary directory.'
    else:
        log('3. Garmin USB Drivers : skipping (only needed for Windows)')

# 4. attempt to install native host
def stage_4():
    global ltxt
    # 4a. copy host files into place
    if os.path.isdir(INSTALL_TMP):
        if os.path.isdir(HOST_DIR): # previously installed; force-update but make backups first
            for f in [x for x in os.listdir(HOST_DIR) if os.path.isfile(x)]: # all files (not subdirs) in host dir
                if not filecmp.cmp(os.path.join(HOST_DIR,f),os.path.join(INSTALL_TMP,'host',f)):
                    # if existing file is not identical to file about to be installed, make a backup
                    # permissions get strange: copying a bak file to the main file will require UAC
                    #  no matter what, as long as the host dir is protected.  This is probably OK.
                    os.makedirs(os.path.join(HOST_DIR,'bak'),exist_ok=True)
                    bakfile=os.path.join(HOST_DIR,'bak',f+'.'+datetime.now().strftime('%Y%m%d-%H%M'))
                    shutil.copyfile(os.path.join(HOST_DIR,f),bakfile)
                    oschmod.set_mode(bakfile,'a+w')
        shutil.copytree(os.path.join(INSTALL_TMP,'host'),HOST_DIR,dirs_exist_ok=True)
        # add edit permissions for all to gpsio-host.* in case the user needs to modify them
        if win32:
            for f in glob.glob(HOST_DIR+'\\gpsio-host.*'):
                oschmod.set_mode(f,'a+w')
        if darwin|linux:
            os.chmod(os.path.join(HOST_DIR,'gpsio-host.py'),stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH) # 755
    else:
        log('4. Native Host : FAILED')
        ltxt+='\n\nNATIVE HOST INSTALLATION FAILED - the temporary installation directory, which should contain the necessary extracted files, does not exist.'
        return

    # 4b. create the host manifest files for each extension
    #       use the system-wide install locations - must run as root / admin
    #       hardcoded per platform in the 'platform dependent constants' section above

    # https://developer.chrome.com/docs/apps/nativeMessaging/#native-messaging-host-location
    # https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_manifests#manifest_location
    # https://docs.microsoft.com/en-us/microsoft-edge/extensions-chromium/developer-guide/native-messaging?tabs=macos#step-3---copy-the-native-messaging-host-manifest-file-to-your-system

    host_path=os.path.join(HOST_DIR,'gpsio-host')
    if win32:
        host_path=host_path.replace('\\','\\\\')
        host_path+='.bat'
    if darwin|linux:
        host_path+='.py'

    # create directories for host manifests, if needed
    for f in HOST_MANIFEST_FILE.values():
        os.makedirs(os.path.dirname(f),exist_ok=True)

    with open(HOST_MANIFEST_FILE['chrome'],'w') as f:
        f.write('{\n  "name": "'+EXTENSION_HANDLE+'",\n  "description": "GPS IO",\n  "path": "'+host_path+'",\n  "type": "stdio",\n  "allowed_origins": [\n    "chrome-extension://'+CHROME_EXTENSION_ID+'/"\n  ]\n}')
    with open(HOST_MANIFEST_FILE['firefox'],'w') as f:
        f.write('{\n  "name": "'+EXTENSION_HANDLE+'",\n  "description": "GPS IO",\n  "path": "'+host_path+'",\n  "type": "stdio",\n  "allowed_extensions": [\n    "'+FIREFOX_EXTENSION_ID+'"\n  ]\n}')
    with open(HOST_MANIFEST_FILE['edge'],'w') as f:
        f.write('{\n  "name": "'+EXTENSION_HANDLE+'",\n  "description": "GPS IO",\n  "path": "'+host_path+'",\n  "type": "stdio",\n  "allowed_origins": [\n    "chrome-extension://'+EDGE_EXTENSION_ID+'/"\n  ]\n}')

    # 4c. Windows: write registry entries for host manifest file locations
    if win32:
        winreg.SetValueEx(winreg.CreateKey(HKCU,CHROME_NMH_KEY),'',0,winreg.REG_SZ,os.path.join(HOST_DIR,'chrome-manifest.json'))
        winreg.SetValueEx(winreg.CreateKey(HKCU,FIREFOX_NMH_KEY),'',0,winreg.REG_SZ,os.path.join(HOST_DIR,'firefox-manifest.json'))
        winreg.SetValueEx(winreg.CreateKey(HKCU,EDGE_NMH_KEY),'',0,winreg.REG_SZ,os.path.join(HOST_DIR,'edge-manifest.json'))
    
    # 4d. edit gpsio-host.ini with confirmed gpsbabel executable path
    #  (this depends on stage 2 having run in the same session!)
    g=findGPSBabel()
    if g[0] and g[1]:
        gpsbabel_exe=g[1]
        with open(os.path.join(HOST_DIR,'gpsio-host.ini'),'r') as f:
            fdata=f.read()
        fdata=fdata.replace('UNDEFINED',gpsbabel_exe)
        with open(os.path.join(HOST_DIR,'gpsio-host.ini'),'w') as f:
            f.write(fdata)

    # 4e. delete unused modules from host dist        
    if win32:
        shutil.rmtree(os.path.join(HOST_DIR,'dist','win32'),ignore_errors=True)
        shutil.rmtree(os.path.join(HOST_DIR,'dist','pywin32_system32'),ignore_errors=True)
        shutil.rmtree(os.path.join(HOST_DIR,'dist','oschmod'),ignore_errors=True)
        
    log('4. Native Host : installed')
    ltxt+='\n\nNative host installed at '+HOST_DIR+'\n'


####################################################################
# top level code: run the requested functions, in alphabetical order
####################################################################
stages.sort()

if any(item in stages for item in ['1a','1b','1c']):
    log('1. Browser Extension(s) :')

# if multiple stages are being done, delete the log file first
if len(stages)>1:
    try:
        os.remove(os.path.join(INSTALL_TMP,'install-notices.txt'))
        os.remove(os.path.join(HOST_DIR,'install-log.txt'))
    except:
        pass
for stage in stages:
    funcName='stage_'+stage
    globals()[funcName]()

if ltxt!='':
    with open(os.path.join(INSTALL_TMP,'install-notices.txt'),'a') as f:
        f.write(ltxt)

exit(0) # required for mac pkgbuild

