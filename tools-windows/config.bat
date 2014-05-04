rem This file contains a list of configurations.
rem You'll probably need to edit them so that it fits to your environment.
rem This file is parsed by a batch script, so beware the syntax if you are
rem doing something fancy.

rem ==========================================================================
rem General
rem ==========================================================================

set PYTHON=C:\Python27\python.exe
set PIP=C:\Python27\Scripts\pip.exe
set INSTALLDIR=%CD%\..\opt
set USERDATADIR=%APPDATA%\kcaa

rem ==========================================================================
rem Proxy
rem ==========================================================================

set PROXYCONTROLLERBIN=%INSTALLDIR%\browsermob-proxy\bin\browsermob-proxy.bat
set PROXYCONTROLLERHOST=localhost
set PROXYCONTROLLERPORT=9090
set PROXYPORT=9091

rem ==========================================================================
rem Server
rem ==========================================================================

set SERVERPORT=0
set BACKENDUPDATEINTERVAL=0.1

rem ==========================================================================
rem Browser
rem ==========================================================================

set KANCOLLEBROWSER=chrome
set KCAABROWSER=chrome
set SHOWKANCOLLE_SCREEN=false
set FRONTENDUPDATEINTERVAL=0.5

rem ==========================================================================
rem Chrome-specific
rem ==========================================================================

set CHROMEBIN=
set CHROMEUSERDATABASEDIR=%USERDATADIR%\chrome
set CHROMEDRIVERBIN=%INSTALLDIR%\chromedriver.exe

rem ==========================================================================
rem PhantomJS-specific
rem ==========================================================================

rem Not supported.
set PHANTOMJSBIN=

rem ==========================================================================
rem Credentials
rem ==========================================================================

rem Not supported.
set CREDENTIALS=

rem ==========================================================================
rem Debug
rem ==========================================================================

set DEBUG=false
