' Launcher Tool Voice Clone (Doanhbadboiz)
' - Lan dau (chua co .venv): chay cai_dat.bat (hien cua so de tai thu vien).
' - Cac lan sau: chay GUI bang pythonw -> KHONG hien cua so console.
Option Explicit
Dim fso, sh, appdir, vpy
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
appdir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = appdir
vpy = appdir & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(vpy) Then
    ' chua cai -> chay cai dat (cho hoan tat)
    sh.Run """" & appdir & "\cai_dat.bat""", 1, True
End If

If fso.FileExists(vpy) Then
    sh.Run """" & vpy & """ """ & appdir & "\tts_gui.py""", 0, False
Else
    MsgBox "Cai dat chua hoan tat. Hay chay cai_dat.bat roi mo lai.", 48, "Tool Voice Clone"
End If
