@echo off

call config.bat

%PROXYCONTROLLERBIN% --port=%PROXYCONTROLLERPORT%
