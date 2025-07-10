; Inno Setup Script for POS Printer Agent
[Setup]
AppName=POS Printer Agent
AppVersion=1.0.0
DefaultDirName={pf}\POSPrinterAgent
DefaultGroupName=POS Printer Agent
OutputDir=.
OutputBaseFilename=POSPrinterAgentInstaller
Compression=lzma
SolidCompression=yes
DisableDirPage=yes

[Files]
Source: "dist\printer_agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\POS Printer Agent"; Filename: "{app}\printer_agent.exe"
Name: "{startup}\POS Printer Agent"; Filename: "{app}\printer_agent.exe"
Name: "{userdesktop}\POS Printer Agent"; Filename: "{app}\printer_agent.exe"

[Run]
Filename: "{app}\printer_agent.exe"; Description: "Launch POS Printer Agent"; Flags: nowait postinstall skipifsilent

[SetupIconFile]
Filename: "icon.ico"
