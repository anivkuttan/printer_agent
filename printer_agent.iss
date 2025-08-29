[Setup]
AppName=LAUNDRY Printer Agent
AppVersion=2.0.2
DefaultDirName={autopf}\LAUNDRYPrinterAgent
DefaultGroupName=LAUNDRY Printer Agent
OutputDir=./dist/
OutputBaseFilename=Laundry_Printer_Agent_Installer-2.0.2
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
SetupIconFile=icon.ico
PrivilegesRequired=admin

[Files]
Source: "dist\laundry_printer_agent_2.0.2.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "src\tools\wkhtmltox\bin\wkhtmltopdf.exe"; DestDir: "{app}\tools\wkhtmltox\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "src\tools\SumatraPDF\SumatraPDF.exe"; DestDir: "{app}\tools\SumatraPDF"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent_2.0.2.exe"
Name: "{commonstartup}\POS Printer Agent"; Filename: "{app}\laundry_printer_agent_2.0.2.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent_2.0.2.exe"

[Run]
Filename: "{app}\laundry_printer_agent_2.0.2.exe"; Description: "Start Agent Now"; Flags: nowait postinstall skipifsilent
