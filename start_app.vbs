' Launcher Tool Voice Clone (Doanhbadboiz)
' - Da cai (co .venv): chay GUI bang pythonw -> KHONG hien cua so console.
' - Chua cai: mo cua so cai dat (cai_dat.bat -> setup_gui.py co thanh tien trinh).
'   setup_gui se mo Tool khi cai xong -> KHONG tu mo o day (tranh mo 2 lan).
Option Explicit
Dim fso, sh, appdir, vpy
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
appdir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = appdir
vpy = appdir & "\.venv\Scripts\pythonw.exe"

If fso.FileExists(vpy) Then
    ' Da cai dat xong -> mo Tool ngay (khong console)
    sh.Run """" & vpy & """ """ & appdir & "\tts_gui.py""", 0, False
Else
    ' Chua cai -> mo cua so cai dat (setup_gui se co nut "Mo Tool")
    sh.Run """" & appdir & "\cai_dat.bat""", 1, True
End If
