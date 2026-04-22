@echo off
REM Windows 构建脚本

echo 正在安装依赖...
pip install -r requirements.txt
pip install pyinstaller

echo 正在构建可执行文件...
pyinstaller picResize.spec --clean

echo 构建完成！
echo 可执行文件位置: dist\picResize.exe
pause
