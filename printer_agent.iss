[Setup]
AppName=LAUNDRY Printer Agent
AppVersion=1.3.0
DefaultDirName={autopf}\LAUNDRYPrinterAgent
DefaultGroupName=LAUNDRY Printer Agent
OutputDir=./dist/
OutputBaseFilename=LAUNDRYPrinterAgentInstaller
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
SetupIconFile=icon.ico
PrivilegesRequired=admin

[Files]
Source: "dist\laundry_printer_agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent.exe"
Name: "{commonstartup}\POS Printer Agent"; Filename: "{app}\laundry_printer_agent.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent.exe"

[Run]
Filename: "{app}\laundry_printer_agent.exe"; Description: "Start Agent Now"; Flags: nowait postinstall skipifsilent


[SetupIconFile]
Filename: "icon.ico"