; GPSIO installer for Windows

; github.com/ncssar/gpsio

; this is a control file for NSIS https://nsis.sourceforge.io

Name "GPSIO"
OutFile "install-gpsio.exe"
InstallDir "$EXEDIR\install-gpsio-tmp"

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
    File "prerequisites\common\*.*"
    File "prerequisites\win\*.*"
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
    DetailPrint "  1a. Chrome Extension : installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} 1a"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Firefox Extension"
    DetailPrint "  1b. Firefox Extension : installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} 1b"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Edge Extension"
    DetailPrint "  1c. Edge Extension : installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} 1c"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "GPSBabel"
    DetailPrint "2. GPSBabel : installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} 2"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Garmin USB Drivers"
    DetailPrint "3. Garmin USB Drivers : installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} 3"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Native Host"
    DetailPrint "4. Native Host : installing..."
    Sleep 1000
    ExecDos::exec /TOSTACK "${py} 4"
    Pop $0 ; status
    Pop $1 ; stdout
    ${DetailUpdate} "$1"
SectionEnd

Section "Cleanup"
    ; view log file in a message box
    ClearErrors
    FileOpen $0 "$INSTDIR\install-notices.txt" r
    ${Do}
        FileRead $0 $1 
        ${If} ${Errors}
            ${ExitDo}
        ${EndIf}
        StrCpy $2 "$2$1"
    ${Loop}
    FileClose $0
    ; contents should now be in $2:
    MessageBox MB_OK "GPSIO Installation Notices:$\r$\rIf any portions of the install failed or had warnings, details will appear here; parts not listed here will work as expected.$2$\r$\rAfter closing the installer, your web browser will show some follow-up instructions you will need to follow to make sure the extensions are working."
SectionEnd

Function .onGUIEnd
    SetOutPath "$INSTDIR\.." # since current outpath can't be deleted
    RMDir /r "$INSTDIR"
    ExecShell "open" "https://github.com/ncssar/gpsio/blob/master/README.md#extensions---installation-follow-up-and-details"
FunctionEnd

