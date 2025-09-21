# 心理学实验程序打包说明

## 概述

本项目提供了多种方式将Python代码打包成可执行文件（exe），方便在没有Python环境的计算机上运行。

## 方法一：使用自动化脚本（推荐）

### Windows用户
1. 双击运行 `build_exe.bat` 文件
2. 等待构建完成
3. 在 `dist` 目录中找到 `心理学实验程序.exe`

### 跨平台用户
1. 运行 `python build_exe.py`
2. 按照提示操作
3. 在 `dist` 目录中找到可执行文件

## 方法二：手动构建

### 1. 安装依赖
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 2. 使用spec文件构建
```bash
pyinstaller --clean build_exe.spec
```

### 3. 或直接使用PyInstaller
```bash
pyinstaller --onefile --windowed --name "心理学实验程序" --add-data "config.json;." --add-data "stimuli.csv;." --add-data "fonts;fonts" --add-data "pictures;pictures" main.py
```

## 文件说明

- `requirements.txt`: 项目依赖列表
- `build_exe.spec`: PyInstaller配置文件，包含所有资源文件设置
- `build_exe.py`: 跨平台自动化构建脚本
- `build_exe.bat`: Windows批处理构建脚本

## 构建输出

构建完成后，你将在 `dist` 目录中找到：
- `心理学实验程序.exe`: 主程序可执行文件
- 所有必要的资源文件会被自动包含

## 故障排除

### 常见问题

1. **构建失败：找不到模块**
   - 确保所有依赖都已安装：`pip install -r requirements.txt`

2. **字体显示异常**
   - 检查 `fonts/SimHei.ttf` 文件是否存在
   - 确保配置文件中的字体路径正确

3. **图片无法加载**
   - 检查 `pictures` 目录下的图片文件是否完整
   - 确保图片格式受支持（PNG、JPG等）

4. **程序启动失败**
   - 检查 `config.json` 配置文件是否存在且格式正确
   - 确保 `stimuli.csv` 数据文件存在

### 手动排除故障

1. **检查Python环境**
   ```bash
   python --version
   pip list
   ```

2. **测试PyInstaller**
   ```bash
   pyinstaller --version
   ```

3. **清理并重新构建**
   ```bash
   # 删除构建文件
   rm -rf build dist *.spec

   # 重新构建
   pyinstaller --clean build_exe.spec
   ```

## 运行要求

### 系统要求
- Windows 7/8/10/11
- macOS 10.12+
- Linux (Ubuntu 16.04+)

### 硬件要求
- 屏幕分辨率：建议1920x1080或更高
- 内存：至少2GB RAM
- 存储空间：至少100MB可用空间

## 高级配置

### 自定义图标
在 `build_exe.spec` 文件中修改：
```python
icon='path/to/your/icon.ico'
```

### 添加其他数据文件
在 `build_exe.spec` 的 `data_files` 列表中添加：
```python
(str(project_root / 'your_file.txt'), '.')
```

### 启用控制台输出（调试用）
在 `build_exe.spec` 中修改：
```python
console=True
```

## 技术支持

如果遇到问题，请：
1. 检查上述故障排除步骤
2. 查看构建过程中的错误信息
3. 确认所有源文件和资源文件完整

## 🎉 构建成功！

### ✅ 构建结果

你的心理学实验程序已经成功打包！在 `dist` 目录中生成了：

- **`心理学实验程序`** (69MB) - 单文件可执行程序
- **`心理学实验程序.app`** - macOS应用程序包

### 🚀 直接使用：
```bash
# 运行单文件程序
./dist/心理学实验程序

# 或双击运行应用程序包
open dist/心理学实验程序.app
```

### 💡 分发说明：
- 将 `dist/心理学实验程序` 文件发送给其他macOS用户即可
- 接收方无需安装Python或其他依赖即可运行
- 建议测试程序在目标机器上的运行效果

## 注意事项

- 首次运行可能需要较长时间
- 确保构建环境和目标环境使用相同或兼容的操作系统
- 建议在干净的Python环境中进行构建
- 构建完成后可以删除 `build` 目录以节省空间
