dir "C:\Program Files\Mantra"
dir "C:\Program Files (x86)\Mantra"
dir "C:\ProgramData\Mantra"

    dir C:\ /s /b | findstr /i mantra



net stop "Mantra MFS110 Registered Device Service" 2>nul
net stop "Mantra Registered Device Service" 2>nul

rmdir /s /q "C:\Program Files\Mantra"
rmdir /s /q "C:\ProgramData\MantraMFS110"
rmdir /s /q "C:\ProgramData\MantraMIS100V2"

reg delete "HKLM\SOFTWARE\Mantra" /f
reg delete "HKLM\SOFTWARE\WOW6432Node\Mantra" /f
