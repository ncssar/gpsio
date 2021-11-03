; GPSIO installer
; github.com/ncssar/gpsio

; !include "MUI.nsh"

Name "GPSIO"
OutFile "install-gpsio.exe"

; Hardcoded ID for a simple test extension: JSONView
!define EXTENSION_ID "chklaanhfefbnpoihckbnefhakgolnmc"

;!define CHROME_EXTENSIONS_FOLDER "${HOME}\AppData\Local\Google\Chrome\User Data\Default\Extensions"
!define CHROME_EXTENSIONS_FOLDER "$LOCALAPPDATA\Google\Chrome\User Data\Default\Extensions"
!define REGISTRY_BASE_KEY "SOFTWARE\WOW6432Node\Google\Chrome\Extensions"
!define REGISTRY_FULL_KEY "${REGISTRY_BASE_KEY}\${EXTENSION_ID}"

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
    IfFileExists "${CHROME_EXTENSIONS_FOLDER}\${EXTENSION_ID}" 0 nofile
        MessageBox MB_OK "It appears the extension is already installed for this user."
        Goto extension_done
    nofile:
        ; test for existence of attempted install-via-registry; see https://nsis-dev.github.io/NSIS-Forums/html/t-288318.html
        ClearErrors
        EnumRegKey $0 HKLM "${REGISTRY_FULL_KEY}" "update_url"
        IfErrors 0 keyexists
            MessageBox MB_OK "Registry key does not exist - click OK to add it..."
            WriteRegStr HKLM "${REGISTRY_FULL_KEY}" "update_url" "https://clients2.google.com/service/update2/crx"
            MessageBox MB_OK "Registry key added.  Chrome may prompt you to enable the extension."
            Goto extension_done
        keyexists:
            MessageBox MB_OK "Registry key already exists, but it does not appear that the extension is installed for this user.  You will need to install the GPSIO extension to Chrome by hand."
    ;        DeleteRegKey HKLM "${REGISTRY_FULL_KEY}"
extension_done:
SectionEnd

Section "GPSBabel"
    MessageBox MB_OK "GPSBabel: Click OK.  Nothing here yet."
SectionEnd

Section "Garmin USB Drivers"
    MessageBox MB_OK "Garmin USB Drivers: Click OK.  Nothing here yet."
SectionEnd

Section "Native Host"
    MessageBox MB_OK "Native Host: Click OK.  Nothing here yet."
SectionEnd

Section "Complete"
    MessageBox MB_OK "Installation complete!"
SectionEnd