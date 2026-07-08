@echo off
echo Mantra cleanup shuru ho raha hai...
echo.

:: Mantra services stop kar
net stop "Mantra MFS110 Registered Device Service" 2>nul
net stop "Mantra Registered Device Service" 2>nul
net stop "MFS100ClientService" 2>nul

echo Services stop ho gayi (agar chal rahi thi)
echo.

:: Program Files se Mantra folder delete kar
if exist "C:\Program Files\Mantra" (
    rmdir /s /q "C:\Program Files\Mantra"
    echo Program Files\Mantra deleted
)

if exist "C:\Program Files (x86)\Mantra" (
    rmdir /s /q "C:\Program Files (x86)\Mantra"
    echo Program Files x86\Mantra deleted
)

:: ProgramData se bhi Mantra related files delete kar
if exist "C:\ProgramData\Mantra" (
    rmdir /s /q "C:\ProgramData\Mantra"
    echo ProgramData\Mantra deleted
)

:: Registry entries clean kar
reg delete "HKLM\SOFTWARE\Mantra" /f 2>nul
reg delete "HKLM\SOFTWARE\WOW6432Node\Mantra" /f 2>nul

echo.
echo Cleanup complete! System restart ho raha hai 10 second mein...
timeout /t 10
shutdown /r /t 0
