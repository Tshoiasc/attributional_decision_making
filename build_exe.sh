#!/bin/bash

echo "=================================================="
echo "心理学实验程序打包工具 (macOS/Linux)"
echo "=================================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python 3，请先安装Python 3.7+"
    exit 1
fi

echo "Python版本: $(python3 --version)"

# 确认操作
read -p "这将清理所有构建文件并重新构建可执行文件。继续？(y/N): " response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "正在清理旧的构建文件..."
rm -rf build dist
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "正在安装依赖..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "依赖安装失败"
    exit 1
fi

python3 -m pip install pyinstaller
if [ $? -ne 0 ]; then
    echo "PyInstaller安装失败"
    exit 1
fi

echo ""
echo "正在构建可执行文件..."
python3 -m pyinstaller --clean build_exe.spec
if [ $? -ne 0 ]; then
    echo "构建失败"
    exit 1
fi

echo ""
echo "=================================================="
echo "打包完成！"
echo "=================================================="

# 显示构建结果
if [ -d "dist" ]; then
    if [ -f "dist/心理学实验程序" ]; then
        echo "可执行文件位于: dist/心理学实验程序"
        file_size=$(stat -f%z "dist/心理学实验程序" 2>/dev/null || stat -c%s "dist/心理学实验程序" 2>/dev/null || echo "unknown")
        if [ "$file_size" != "unknown" ]; then
            file_size_mb=$(echo "scale=1; $file_size / 1048576" | bc 2>/dev/null || echo "计算失败")
            echo "文件大小: ${file_size_mb} MB"
        fi
    else
        echo "警告：未找到预期的可执行文件"
        ls -la dist/
    fi
else
    echo "错误：dist目录未创建"
fi

echo ""
echo "=================================================="
