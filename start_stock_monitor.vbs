' 启动股票行情监控系统

' 创建WScript.Shell对象
Set objShell = CreateObject("WScript.Shell")

' 获取脚本所在目录
strScriptPath = WScript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

' 切换到脚本所在目录
objShell.CurrentDirectory = strScriptDir

' 杀死所有现有的background_service进程
On Error Resume Next
Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcessList = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'python.exe'")

For Each objProcess in colProcessList
    ' 检查命令行参数是否包含background_service
    If InStr(objProcess.CommandLine, "background_service") > 0 Then
        objProcess.Terminate()
    End If
Next
On Error GoTo 0

' 等待2秒，确保进程完全关闭
WScript.Sleep 2000

' 启动Flask应用
objShell.Run "cmd /c start ""Flask App"" python app.py", 0, False

' 等待3秒，确保Flask应用已经启动
WScript.Sleep 3000

' 启动后台服务
objShell.Run "cmd /c start ""Background Service"" python background_service.py", 0, False

' 等待5秒，确保服务完全启动
WScript.Sleep 5000

' 自动打开浏览器访问股票监控系统
objShell.Run "http://localhost:5000/"

' 显示启动成功的提示信息
objShell.Popup "股票行情监控系统已启动（已清理旧进程）", 2, "启动成功", 64
