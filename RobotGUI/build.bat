set PIP=C:\Python27\Scripts\pyInstaller.exe
%PIP% MainGUI.py --onefile
//python %PIP%Makespec.py --onefile --noconsole --upx MainGUI.py
//python %PIP%Build.py MainGUI.spec