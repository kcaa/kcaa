@ECHO OFF
rem Cited from http://scripting.cocolog-nifty.com/blog/2007/05/tee_0423.html
rem I can't find an info about the author, but big thanks to him/her!

SETLOCAL
SET X=%*
IF NOT DEFINED X (
ECHO Usage: %~nx0 output_file
GOTO :EOF
)
IF "%~0"=="%~dp0.\%~nx0" GOTO :SUB
MORE >%1 | "%~dp0.\%~nx0" %1
GOTO :EOF
:SUB
SET SS=0
SET LL=0
:TOP
IF %SS%==%~z1 (
rem SLEEP 1
ping localhost -n 2 >NUL
CMD /C "TYPE NUL>>%1" 2>NUL
IF NOT ERRORLEVEL 1 GOTO :EOF
GOTO :TOP
)
SET SS=%~z1
FOR /F "delims=[] tokens=1*" %%1 IN ('FIND /N /V "" ^<%1 ^|MORE +%%LL%%') DO (
SET LL=%%1
ECHO:%%2
)
GOTO :TOP
