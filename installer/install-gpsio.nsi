; GPSIO installer
; github.com/ncssar/gpsio

; TODO: move the OS-agnostic portions to a single python script - see old install.py
; TODO: decide on best way to deal with Chrome/Edge extension-registry-trigger key added but extension not installed
;          (probably blocklisted or offline)
; TODO: general cleanup and UI/UX work
;    - closing notes
;    - welcome page instead of messagebox?
; TODO: test, get feedback

; !include "MUI.nsh"

Name "GPSIO"
OutFile "install-gpsio.exe"
InstallDir "$EXEDIR\tmp"

!include LogicLib.nsh
!include nsdialogs.nsh

; from https://nsis.sourceforge.io/DetailUpdate
Function DetailUpdate
  Exch $R0
  Push $R1
  Push $R2
  Push $R3
 
  FindWindow $R2 `#32770` `` $HWNDPARENT
  GetDlgItem $R1 $R2 1006
  SendMessage $R1 ${WM_SETTEXT} 0 `STR:$R0`
  GetDlgItem $R1 $R2 1016
 
  System::Call *(&t${NSIS_MAX_STRLEN}R0)i.R2
  System::Call *(i0,i0,i0,i0,i0,iR2,i${NSIS_MAX_STRLEN},i0,i0)i.R3
 
;   !define LVM_GETITEMCOUNT 0x1004 - already defined in WinMessages.nsh
;   !define LVM_SETITEMTEXT 0x102E - already defined in WinMessages.nsh
  SendMessage $R1 ${LVM_GETITEMCOUNT} 0 0 $R0
  IntOp $R0 $R0 - 1
  System::Call user32::SendMessage(iR1,i${LVM_SETITEMTEXT},iR0,iR3)
 
  System::Free $R3
  System::Free $R2
 
  Pop $R3
  Pop $R2
  Pop $R1
  Pop $R0
FunctionEnd

!macro DetailUpdate Text
  Push `${Text}`
  Call DetailUpdate
!macroend
!define DetailUpdate `!insertmacro DetailUpdate`

ShowInstDetails show

Section "Startup"
    DetailPrint "Extracting required files..."
    SetDetailsPrint none
    SetOutPath "$INSTDIR"
    File "install-gpsio.py"
    File "prerequisites\*.*"
    SetOutPath "$INSTDIR\host"
    File /r "..\host\dist"
    File "..\host\gpsio-host.ini"
    File "..\host\gpsio-host.bat"
    File "..\host\gpsio-host.py"
    File "README.txt" ; not the same as README.md which is for the GitHub repo page
    SetDetailsPrint both
    ${DetailUpdate} "Extracting required files... Done."
    MessageBox MB_OK "Click OK to install all GPSIO components."
    DetailPrint "1. Web Browser Extensions"
    Sleep 500
SectionEnd

ShowInstDetails show

!define py "$INSTDIR/host/dist/python.exe $INSTDIR/install-gpsio.py"

Section "Chrome Extension"
    DetailPrint "  1a. Chrome Extension --> installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} -min 1a"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Firefox Extension"
    DetailPrint "  1b. Firefox Extension --> installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} -min 1b"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Edge Extension"
    DetailPrint "  1c. Edge Extension --> installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} -min 1c"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "GPSBabel"
    DetailPrint "2. GPSBabel --> installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} -min 2"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Garmin USB Drivers"
    DetailPrint "3. Garmin USB Drivers --> installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} -min 3"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Native Host"
    DetailPrint "4. Native Host --> installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} -min 4"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Cleanup"
    ExecDos::exec "${py} -min 5" # cleanup of items that python is aware of
SectionEnd

Function .onGUIEnd
    SetOutPath "$INSTDIR\.." # since outpath can't be deleted
    RMDir /r "$INSTDIR"
FunctionEnd
