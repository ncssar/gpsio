; GPSIO installer
; github.com/ncssar/gpsio

; !include "MUI.nsh"

Name "GPSIO"
OutFile "install-gpsio.exe"
InstallDir "$PROFILE\install-gpsio-out"

; Hardcoded ID for a simple test extension: JSONView
!define EXTENSION_ID "chklaanhfefbnpoihckbnefhakgolnmc"

;!define CHROME_EXTENSIONS_FOLDER "${HOME}\AppData\Local\Google\Chrome\User Data\Default\Extensions"
!define CHROME_EXTENSIONS_FOLDER "$LOCALAPPDATA\Google\Chrome\User Data\Default\Extensions"
!define REGISTRY_BASE_KEY "SOFTWARE\WOW6432Node\Google\Chrome\Extensions"
!define REGISTRY_FULL_KEY "${REGISTRY_BASE_KEY}\${EXTENSION_ID}"
!define UNINSTALL_ROOT "SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"

;CheckUninstallKey - checks to see if there is an uninstall key with specified entry name and value
;  return value of 'NOT FOUND' or 'FOUND!' is passed on the stack
!macro CheckUninstallKey entryName entryVal
    DetailPrint "Checking for uninstall key:"
    DetailPrint "  entry name:${entryName}  entry value:${entryVal}"
    !define ID ${__LINE__} ; get around duplicated labels; see https://nsis.sourceforge.io/Macro_vs_Function example 3.1.3
    StrCpy $0 0
    StrCpy $4 "NOT FOUND" ; default result
    loop_${ID}:
        EnumRegKey $1 HKLM "${UNINSTALL_ROOT}" $0
        StrCmp $1 "" done_${ID} ; empty string indicates no more entries
        ; DetailPrint "  Loop iteration $0: $1"
        ClearErrors
        ReadRegStr $2 HKLM "${UNINSTALL_ROOT}\$1" "${entryName}"
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
        Push $4
        !undef ID ; see comment on !define ID above
!macroend

Section "Startup"
    SetOutPath "$INSTDIR"
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
        EnumRegKey $0 HKLM "${REGISTRY_FULL_KEY}" "update_url"
        IfErrors 0 keyexists2
            MessageBox MB_OK "Registry key does not exist - click OK to add it..."
            WriteRegStr HKLM "${REGISTRY_FULL_KEY}" "update_url" "https://clients2.google.com/service/update2/crx"
            MessageBox MB_OK "Registry key added.  Chrome may prompt you to enable the extension."
            Goto extension_done
        keyexists2:
            MessageBox MB_OK "Registry key already exists, but it does not appear that the extension is installed for this user.  You will need to install the GPSIO extension to Chrome by hand."
    ;        DeleteRegKey HKLM "${REGISTRY_FULL_KEY}"
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
    !insertMacro CheckUninstallKey "DisplayName" "GPSBabel 1.7.0"
    Pop $0
    DetailPrint "GPSBabel: $0"
    StrCmp $0 "FOUND!" gpsbabel_done
        MessageBox MB_OK "Click OK to launch the GPSBabel Installer..."
        File "prerequisites\GPSBabel-1.7.0-Setup.exe"
        ExecWait "$OUTDIR\GPSBabel-1.7.0-Setup.exe"
    gpsbabel_done:
SectionEnd

Section "Garmin USB Drivers"
    !insertMacro CheckUninstallKey "DisplayName" "Garmin USB Drivers"
    Pop $0
    DetailPrint "Garmin USB Drivers: $0"
    StrCmp $0 "FOUND!" usb_done
        MessageBox MB_OK "Click OK to launch the Garmin USB Drivers Installer..."
        File "prerequisites\USBDrivers_2312.exe"
        ExecWait "$OUTDIR\USBDrivers_2312.exe"
    usb_done:
SectionEnd

Section "Native Host"
    MessageBox MB_OK "Click OK to install the native host..."
    SetOutPath "$PROFILE\gpsio_install_test"
    File /r "..\host\dist"
    File "..\host\gpsio-host.ini"
    File "..\host\gpsio-host.bat"
    File "..\host\README.txt"
    ; TODO: edit gpsio-host.ini with confirmed gpsbabel executable path
    ; TODO: generate chrome-manifest.json and firefox-manifest.json
    ; TODO: edit registry, to register the native host manifest location
    ; TODO: set correct install path
SectionEnd

Section "Complete"
    ; TODO: delete temp files (GPSBabel installer, Garmin USB driver installer)
    MessageBox MB_OK "Installation complete!"
SectionEnd
