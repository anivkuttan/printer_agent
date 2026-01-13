Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\Users\anivk\CCS\laundry\printer_agent\run_printer_service.bat" & chr(34), 0
Set WshShell = Nothing
