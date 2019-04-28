@echo off
SETLOCAL
SET SETTINGS=
python %USERPROFILE%\bin\gitSync.py %SETTINGS% %*
