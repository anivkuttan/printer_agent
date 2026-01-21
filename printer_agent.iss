; -----------------------------------------------------------
; LAUNDRY Printer Agent Installer
; -----------------------------------------------------------

[Setup]
AppName=LAUNDRY Printer Agent
AppVersion=10.0.0
DefaultDirName={autopf}\LAUNDRYPrinterAgent
DefaultGroupName=LAUNDRY Printer Agent
OutputDir=./dist/
OutputBaseFilename=Laundry_Printer_Agent_Installer-10.0.0
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
SetupIconFile=icon.ico
PrivilegesRequired=admin
UninstallDisplayIcon={app}\icon.ico

; -----------------------------------------------------------
; Files
; -----------------------------------------------------------
[Files]
Source: "dist\laundry_printer_agent_10.0.0.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

Source: "src\tools\wkhtmltox\bin\wkhtmltopdf.exe"; \
    DestDir: "{app}\tools\wkhtmltox\bin"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: "src\tools\SumatraPDF\SumatraPDF.exe"; \
    DestDir: "{app}\tools\SumatraPDF"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: ".env"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion


; -----------------------------------------------------------
; Register Custom URL Protocol (laundryagent://)
; -----------------------------------------------------------
[Registry]
Root: HKCR; Subkey: "laundryagent"; ValueType: string; ValueName: ""; ValueData: "URL:LAUNDRY Printer Agent Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "laundryagent"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "laundryagent\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\icon.ico"
Root: HKCR; Subkey: "laundryagent\shell\open\command"; ValueType: string; ValueName: ""; \
    ValueData: """{app}\laundry_printer_agent_10.0.0.exe"" ""%1"""

; -----------------------------------------------------------
; Auto-start at Windows login (BETTER than Startup shortcut)
; -----------------------------------------------------------
[Registry]
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; \
    ValueName: "LaundryPrinterAgent"; ValueType: string; \
    ValueData: """{app}\laundry_printer_agent_10.0.0.exe"""; Flags: uninsdeletevalue

; -----------------------------------------------------------
; Shortcuts
; -----------------------------------------------------------
[Icons]
Name: "{group}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent_10.0.0.exe"
Name: "{commondesktop}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent_10.0.0.exe"

; (Startup folder shortcut is removed — registry auto-start is more reliable)

; -----------------------------------------------------------
; Run on Finish
; -----------------------------------------------------------
[Run]
Filename: "{app}\laundry_printer_agent_10.0.0.exe"; \
    Description: "Start Agent Now"; \
    Flags: nowait postinstall skipifsilent

; -----------------------------------------------------------
; Uninstall cleanup
; -----------------------------------------------------------
[UninstallDelete]
Type: files; Name: "{app}\update.tmp"
Type: filesandordirs; Name: "{app}"
