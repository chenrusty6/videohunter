Set WshShell = CreateObject("WScript.Shell")
Dim fso, currentDirectory, pyw
Set fso = CreateObject("Scripting.FileSystemObject")
currentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDirectory

If fso.FileExists(currentDirectory & "\runtime\pythonw.exe") Then
    pyw = """" & currentDirectory & "\runtime\pythonw.exe"""
Else
    pyw = "pythonw.exe"
End If

WshShell.Run pyw & " server.py", 0, False
