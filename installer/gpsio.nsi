; GPSIO installer
; github.com/ncssar/gpsio

; !include "MUI.nsh"

Name "GPSIO"
OutFile "install-gpsio.exe"
InstallDir "$PROFILE\gpsio"

; ReplaceInFile - see https://nsis.sourceforge.io/ReplaceInFile
!include StrRep.nsh
!include ReplaceInFile.nsh

; TODO - replace the temp ID afgce... (old gpsio extension) when new one is published
!define EXTENSION_ID "afgcejeehpnhafgikkimogllebbgegck"
!define CHROME_EXTENSIONS_FOLDER "$LOCALAPPDATA\Google\Chrome\User Data\Default\Extensions"
!define CHROME_REGISTRY_BASE_KEY "SOFTWARE\WOW6432Node\Google\Chrome\Extensions"
!define CHROME_REGISTRY_FULL_KEY "${CHROME_REGISTRY_BASE_KEY}\${EXTENSION_ID}"
!define UNINSTALL_ROOT "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
!define UNINSTALL_WOW_ROOT "SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"

Var GPSBABEL_EXE_PATH
Var INSTDIR_DOUBLE_SLASH

!macro FindRegKeyWithEntry rootKey entryName entryVal
    DetailPrint "Checking for sub-key:"
    DetailPrint " root key:${rootKey}"
    DetailPrint " entry name:${entryName}  entry value:${entryVal}"
    !define ID ${__LINE__} ; get around duplicated labels; see https://nsis.sourceforge.io/Macro_vs_Function example 3.1.3
    StrCpy $0 0
    StrCpy $4 "NOT FOUND" ; default result
    loop_${ID}:
        EnumRegKey $1 HKLM "${rootKey}" $0
        StrCmp $1 "" done_${ID} ; empty string indicates no more entries
        ; DetailPrint "  Loop iteration $0: $1"
        ClearErrors
        ReadRegStr $2 HKLM "${rootKey}\$1" "${entryName}"
        IfErrors 0 keyexists_${ID} ; if the specified sub-key does not exist
            ; DetailPrint "    no such entry"
            Goto next_${ID}
        keyexists_${ID}: ; else
            ; DetailPrint "    ${entryName}=$2"
            StrCmp $2 "${entryVal}" found_${ID} ; this is not a regular expression - exact match required
        next_${ID}:
            IntOp $0 $0 + 1
            Goto loop_${ID}
        found_${ID}:
            StrCpy $4 "FOUND!"
            DetailPrint "    FOUND under key $1"
    done_${ID}:
        DetailPrint "  loop complete: $4"
        ; push the uninstall sub-key name (if any), and the result string
        Push $1
        Push $4
        !undef ID ; see comment on !define ID above
!macroend

; TODO: prompt for install dir

Section "Startup"
    SetOutPath "$INSTDIR"
    StrCpy $GPSBABEL_EXE_PATH "DEFAULT" ; to avoid warning during compile
    ${StrRep} $INSTDIR_DOUBLE_SLASH $INSTDIR "\" "\\"
    SetRegView 64 ; to allow viewing of both the WOW64 and non-WOW64 parts of the registry
      ; (necessary to find Garmin USB drivers)
SectionEnd

; 1. is the extension already installed?
;      look for a folder whose name is EXTENSION_ID, in the user's extensions dir
; 1a. if yes, skip to 2
; 1b. if no, check to see if install via registry has already been attempted
; 1b1. if yes, show a warning message that extension install failed, user must install by hand, skip to 2
; 1b2. if no, add the registry entry to attemp extension installation
; 2. check again and let the user know if the extension is apparently installed (is Chrome restart required??)
; 3. 

Section "Chrome Extension"
    ; 1. is the extension already installed?
    IfFileExists "${CHROME_EXTENSIONS_FOLDER}\${EXTENSION_ID}" 0 nofile1
        MessageBox MB_OK "It appears the extension is already installed for this user."
        Goto extension_done
    nofile1:
        ; test for existence of attempted install-via-registry; see https://nsis-dev.github.io/NSIS-Forums/html/t-288318.html
        ClearErrors
        EnumRegKey $0 HKLM "${CHROME_REGISTRY_FULL_KEY}" "update_url"
        IfErrors 0 keyexists2
            MessageBox MB_OK "Registry key does not exist - click OK to add it..."
            WriteRegStr HKLM "${CHROME_REGISTRY_FULL_KEY}" "update_url" "https://clients2.google.com/service/update2/crx"
            MessageBox MB_OK "Registry key added.  Chrome may prompt you to enable the extension."
            Goto extension_done
        keyexists2:
            MessageBox MB_OK "Registry key already exists, but it does not appear that the extension is installed for this user.  You will need to install the GPSIO extension to Chrome by hand."
    ;        DeleteRegKey HKLM "${CHROME_REGISTRY_FULL_KEY}" - not sure if there is a real need to delete the key
    extension_done:
SectionEnd

Section "GPSBabel"
    ; is it already installed? test for registry entry
    ;  the GPSBabel installer doesn't check to see if it's already installed,
    ;   and it doesn't let you specify the installation directory.
    ;  if installed, these keys should exist:
    ;  HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{blahblah}
    ;     (there are lots of these - one per installed item - one of them should have DisplayName = "GPSBabel <version>")
    ;     (the correct one will have the installation directory)
    ;  HKEY_USERS\blahblah\SOFTWARE\GPSBabel - this has sub-keys GPSBabel (with a bunch of settings) and GPSBabelFE (empty)
    ;  and a handful of other registry entries that seem more temporary / less robust;
    ;  maybe easier to just look for the executable in the standard installation directory?
    !insertMacro FindRegKeyWithEntry "${UNINSTALL_WOW_ROOT}" "DisplayName" "GPSBabel 1.7.0"
    Pop $0 ; FOUND! or NOT FOUND
    Pop $1 ; sub-key name if found
    DetailPrint "GPSBabel: $0"
    StrCmp $0 "FOUND!" gpsbabel_find_exe
        MessageBox MB_OK "Click OK to launch the GPSBabel Installer..."
        SetOutPath "$INSTDIR\tmp"
        File "prerequisites\GPSBabel-1.7.0-Setup.exe"
        ExecWait "$OUTDIR\GPSBabel-1.7.0-Setup.exe"
        ; check the registry again after install; it should be there now if it wasn't before!
        !insertMacro FindRegKeyWithEntry "${UNINSTALL_WOW_ROOT}" "DisplayName" "GPSBabel 1.7.0"
    gpsbabel_find_exe:
        ; read the expected file path from the registry, then confirm it
        ReadRegStr $0 HKLM "${UNINSTALL_WOW_ROOT}\$1" "InstallLocation"
        IfFileExists "$0\gpsbabel.exe" 0 gpsbabel_notfound
            StrCpy $GPSBABEL_EXE_PATH "$0\gpsbabel.exe"
            GoTo gpsbabel_done
        gpsbabel_notfound:
            DetailPrint "ERROR: GPSBabel executable was not found at $0\gpsbabel.exe!"
    gpsbabel_done:
SectionEnd

Section "Garmin USB Drivers"
    !insertMacro FindRegKeyWithEntry "${UNINSTALL_ROOT}" "DisplayName" "Garmin USB Drivers"
    Pop $0
    DetailPrint "Garmin USB Drivers: $0"
    StrCmp $0 "FOUND!" usb_done
        MessageBox MB_OK "Click OK to launch the Garmin USB Drivers Installer..."
        SetOutPath "$INSTDIR\tmp"
        File "prerequisites\USBDrivers_2312.exe"
        ExecWait "$OUTDIR\USBDrivers_2312.exe"
    usb_done:
SectionEnd

Section "Native Host"
    MessageBox MB_OK "Click OK to install the native host..."
    SetOutPath "$INSTDIR"
    File /r "..\host\dist"
    File "..\host\gpsio-host.ini"
    File "..\host\gpsio-host.bat"
    File "README.txt" ; not the same as README.md which is for the GitHub repo page

    ; generate chrome-manifest.json and firefox-manifest.json
    ; Common errors in the manifest:
    ;  1 - \ is an escape character in json; use \\ instead
    ;  2 - must have a trailing slash / at the end of the extension ID
    FileOpen $0 $INSTDIR\chrome-manifest.json w
    FileWrite $0 '{$\n  "name": "com.caltopo.gpsio",$\n  "description": "GPS IO",$\n  "path": "$INSTDIR_DOUBLE_SLASH\\gpsio-host.bat",$\n  "type": "stdio",$\n  "allowed_origins": [$\n    "chrome-extension://${EXTENSION_ID}/"$\n  ]$\n}'
    FileClose $0

    FileOpen $0 $INSTDIR\firefox-manifest.json w
    FileWrite $0 '{$\n  "name": "com.caltopo.gpsio",$\n  "description": "GPS IO",$\n  "path": "$INSTDIR_DOUBLE_SLASH\\gpsio-host.bat",$\n  "type": "stdio",$\n  "allowed_extensions": [$\n    "gpsio@caltopo.com"$\n  ]$\n}'
    FileClose $0

    ; edit registry, to register the Chrome and Firefox native host manifest locations
    WriteRegStr HKCU "Software\Google\Chrome\NativeMessagingHosts\com.caltopo.gpsio" "" "$INSTDIR\chrome-manifest.json"
    WriteRegStr HKCU "Software\Mozilla\NativeMessagingHosts\com.caltopo.gpsio" "" "$INSTDIR\firefox-manifest.json"

    ; edit gpsio-host.ini with confirmed gpsbabel executable path
    !insertMacro _ReplaceInFile "$INSTDIR\gpsio-host.ini" "UNDEFINED" "$GPSBABEL_EXE_PATH"
    Delete "$INSTDIR\gpsio-host.ini.old" ; left in place by ReplaceInFile; get rid of it after this simple edit
SectionEnd

Section "Complete"
    RMDir /r "$INSTDIR\tmp"
    MessageBox MB_OK "Installation complete!"
SectionEnd
