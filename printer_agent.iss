[Setup]
AppName=LAUNDRY Printer Agent
AppVersion=5.1.0
DefaultDirName={autopf}\LAUNDRYPrinterAgent
DefaultGroupName=LAUNDRY Printer Agent
OutputDir=./dist/
OutputBaseFilename=Laundry_Printer_Agent_Installer-5.1.0
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
SetupIconFile=icon.ico
PrivilegesRequired=admin

[Files]
Source: "dist\laundry_printer_agent_5.1.0.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "src\tools\wkhtmltox\bin\wkhtmltopdf.exe"; DestDir: "{app}\tools\wkhtmltox\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "src\tools\SumatraPDF\SumatraPDF.exe"; DestDir: "{app}\tools\SumatraPDF"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent_5.1.0.exe"
Name: "{commonstartup}\POS Printer Agent"; Filename: "{app}\laundry_printer_agent_5.1.0.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent_5.1.0.exe"

[Run]
Filename: "{app}\laundry_printer_agent_5.1.0.exe"; Description: "Start Agent Now"; Flags: nowait postinstall skipifsilent
