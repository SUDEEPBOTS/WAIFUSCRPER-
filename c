dir "C:\Program Files\Mantra"
dir "C:\Program Files (x86)\Mantra"
dir "C:\ProgramData\Mantra"

    dir C:\ /s /b | findstr /i mantra
