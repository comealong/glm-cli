# glm-cli

使用智谱官方 API 调用 `GLM-4.6V-Flash` 的命令行工具。

## 安装

推荐使用 `uv`：

```powershell
cd glm-cli
uv tool install .
```

如果修改源码后需要重装：

```powershell
uv tool install --force .
```

也可以开发模式安装：

```powershell
uv tool install --editable .
```

安装完成后：

```powershell
glm --help
```

## API Key

当前版本读取官方推荐环境变量：

```powershell
$env:ZAI_API_KEY="你的_API_Key"
```

PowerShell 永久写入当前 Windows 用户：

```powershell
[Environment]::SetEnvironmentVariable("ZAI_API_KEY", "你的_API_Key", "User")
```

写入后需要重新打开终端。

## 使用

纯文本：

```powershell
glm "解释一下什么是蒙皮动画"
```

本地图片：

```powershell
glm -i .\test.png "详细分析这张图片"
```

多张本地图片：

```powershell
glm -i .\a.png -i .\b.png "比较这两张图"
```

网络图片：

```powershell
glm -i "https://example.com/test.png" "描述图片"
```

关闭深度思考：

```powershell
glm --thinking disabled "快速回答这个问题"
```

显示思考字段：

```powershell
glm --show-thinking -i .\test.png "分析图片"
```

非流式：

```powershell
glm --no-stream "你好"
```

管道输入：

```powershell
Get-Content .\prompt.txt -Raw | glm
```

视频 URL：

```powershell
glm --video "https://example.com/demo.mp4" "总结视频"
```

文件 URL：

```powershell
glm --file "https://example.com/demo.pdf" "总结文档"
```

## 说明

- 模型固定为 `glm-4.6v-flash`。
- 默认启用流式输出。
- 默认开启 `thinking`。
- 本地图片会自动读取并编码为 Base64。
- 本地视频和本地普通文件没有做上传流程，目前请传 URL。
- 按智谱官方说明，同一个请求中不要混用图片、视频和文件三种输入类型。
