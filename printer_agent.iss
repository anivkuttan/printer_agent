[Setup]
AppName=LAUNDRY Printer Agent
AppVersion=1.0.2
DefaultDirName={autopf}\LAUNDRYPrinterAgent
DefaultGroupName=LAUNDRY Printer Agent
OutputDir=./dist/
OutputBaseFilename=LAUNDRYPrinterAgentInstaller
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
SetupIconFile=icon.ico
PrivilegesRequired=admin


[Icons]
Name: "{group}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent.exe"
Name: "{commonstartup}\POS Printer Agent"; Filename: "{app}\laundry_printer_agent.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\LAUNDRY Printer Agent"; Filename: "{app}\laundry_printer_agent.exe"
