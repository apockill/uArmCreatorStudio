REM Get the PyInstaller path
set PYINSTALLER=C:\Python34\Scripts\pyinstaller.exe


REM Create the executable
REM python %PIP%Makespec.py --onefile  --noconsole --upx --name "uArmCreatorStudio" uArmCreatorStudio.spec
%PYINSTALLER% --onefile Build.spec
 
PAUSE


REM Check if the build finished, if it did, delete "Latest Build" before renaming "dist"
if exist "dist/uArmCreatorStudio.exe" RD /S /Q "Latest Build"


REM Rename dist to Latest Build
rename "dist" "Latest Build"


REM Delete the 'build' folder after building
RD /S /Q build


REM Delete the '__pycache__' folder after building
RD /S /Q "__pycache__"


REM Create a folder for storing the uArm's communication protocol
mkdir "Latest Build\Upload This To Your uArm"


REM Copy the communication protocol to this folder
xcopy /isvy "F:\Google Drive\Projects\Arduino Code\uArmCommunicationProtocol_1" "Latest Build\Upload This To Your uArm\uArmCommunicationProtocol_1"


REM Create the "Import Libraries" folder
mkdir "Latest Build\Upload This To Your uArm\Libraries To Import"


REM Copy the uArm library to the "Import Libraries" Folder
xcopy /isvy "F:\Google Drive\Projects\Arduino Code\libraries\UArmForArduino-1.6.0" "Latest Build\Upload This To Your uArm\Libraries To Import\UArmForArduino-1.6.0"


PAUSE