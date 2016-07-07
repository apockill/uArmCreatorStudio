REM Compile all the icons into the the CompiledImages.py 
pyrcc5 "Resources/Images.qrc" -o "Resources/CompiledImages.py"



REM Get the PyInstaller path
set PYINSTALLER=C:\Python34\Scripts\pyinstaller.exe


REM Create the executable
REM python %PIP%Makespec.py --onefile --noconsole --upx MainGUI.py
%PYINSTALLER% --onefile --name "uArmCreatorStudio" --icon="exe_icon.ico" MainGUI.py
 

REM Check if the build finished, if it did, delete "Latest Build" before renaming "dist"
if exist "dist/uArmCreatorStudio.exe" RD /S /Q "Latest Build"
 


REM Rename 'dist' folder to "Latest Build"
rename dist "Latest Build"

REM Re


REM Delete the .spec file after building
DEL uArmCreatorStudio.spec


REM Delete the 'build' folder after building
RD /S /Q build


REM Delete the '__pycache__' folder after building
RD /S /Q "__pycache__"

PAUSE

 