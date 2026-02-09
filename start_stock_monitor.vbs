' 启动股票行情监控系统

' 创建WScript.Shell对象
Set objShell = CreateObject("WScript.Shell")

' 获取脚本所在目录
strScriptPath = WScript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

' 切换到脚本所在目录
objShell.CurrentDirectory = strScriptDir

' 启动Flask应用
objShell.Run "cmd /c start ""Flask App"" python app.py", 0, False

' 等待3秒，确保Flask应用已经启动
WScript.Sleep 3000

' 启动后台服务
objShell.Run "cmd /c start ""Background Service"" python background_service.py", 0, False

' 显示启动成功的提示信息
objShell.Popup "股票行情监控系统已启动", 2, "启动成功", 64
