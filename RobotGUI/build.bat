set PIP=C:\Python34\Scripts\pyinstaller.exe
%PIP% MainGUI.py --onefile

//python %PIP%Makespec.py --onefile --noconsole --upx MainGUI.py
//python %PIP%Build.py MainGUI.spec