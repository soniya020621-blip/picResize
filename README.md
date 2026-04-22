# 图片批量缩放工具

基于 Flask + Vue 3 的图片批量缩放 Web 应用，支持多图片、多尺寸一键导出。

## 功能特性

- **批量上传**：支持拖拽或点击上传多张图片
- **预设尺寸**：内置常用尺寸（头像、电商详情页、主图等）
- **自定义尺寸**：灵活添加任意尺寸
- **智能裁剪**：自动选择最小裁剪量，或手动指定裁剪方向
- **格式选择**：支持 JPEG 和 PNG 输出
- **一键导出**：所有结果打包为 ZIP 文件下载

## 使用方法

### 方式一：直接运行源码

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python web_app.py
```

启动后自动打开浏览器访问 http://localhost:5000

### 方式二：下载可执行程序

前往 [Releases](https://github.com/soniya020621-blip/picResize/releases) 页面下载对应平台的可执行文件：

- **Windows**: `picResize.exe`
- **macOS**: `picResize`

双击运行即可，浏览器会自动打开。

## 自行构建

### 本地构建

在对应平台上运行构建脚本：

**macOS:**
```bash
./build.sh
```

**Windows:**
```cmd
build.bat
```

### GitHub Actions 自动构建（推荐）

无需 Windows 电脑，利用 GitHub 免费资源自动构建双平台版本：

1. 将代码推送到 GitHub
2. 创建 tag 触发构建：
   ```bash
   git tag v1.0.0
   git push --tags
   ```
3. 等待 Actions 完成，在 Releases 页面下载

也可以在 GitHub 仓库页面 → Actions → Build Executables → Run workflow 手动触发。

## 项目结构

```
picResize/
├── web_app.py           # Flask Web 应用入口
├── image_processor.py   # 图片处理核心逻辑
├── config.py            # 预设尺寸配置
├── requirements.txt     # Python 依赖
├── picResize.spec       # PyInstaller 打包配置
├── build.sh             # macOS 构建脚本
├── build.bat            # Windows 构建脚本
├── templates/
│   └── index.html       # 前端页面模板
├── static/
│   ├── css/style.css    # 样式文件
│   └── js/app.js        # Vue.js 前端逻辑
└── .github/workflows/
    └── build.yml        # GitHub Actions 自动构建配置
```

## 技术栈

- **后端**：Flask + Pillow
- **前端**：Vue 3 + 原生 CSS
- **打包**：PyInstaller

## 依赖

- Flask >= 2.0
- Pillow >= 8.0
- PyInstaller >= 5.0（仅打包时需要）
