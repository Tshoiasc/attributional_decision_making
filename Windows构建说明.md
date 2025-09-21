# 在macOS上构建Windows EXE

## 推荐方法：GitHub Actions (最简单)

### 1. 准备GitHub仓库
```bash
# 初始化Git仓库（如果还没有的话）
git init
git add .
git commit -m "Initial commit"

# 创建GitHub仓库并推送
# 访问 https://github.com/new 创建新仓库
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2. 自动构建
- 推送代码后，GitHub Actions会自动开始构建
- 转到你的GitHub仓库页面
- 点击 "Actions" 标签
- 选择最新的工作流运行
- 下载构建好的EXE文件（在Artifacts中）

### 3. 获取EXE文件
1. 在GitHub仓库中点击 **Actions** 标签
2. 选择最新的构建工作流
3. 点击 **windows-exe** 下载构件
4. 解压后获得 `心理学实验程序.exe`

## 备用方法：本地Docker构建

### 1. 安装Docker
```bash
# 下载并安装Docker Desktop for Mac
# https://docs.docker.com/desktop/install/mac/
```

### 2. 运行构建脚本
```bash
python3 build_windows_local.py
# 选择选项2 (Docker方法)
```

### 3. 获取EXE文件
构建完成后，EXE文件将位于 `dist/心理学实验程序.exe`

## 文件说明

- `.github/workflows/build-windows.yml` - GitHub Actions配置文件
- `build_windows_local.py` - 本地构建脚本
- `Windows构建说明.md` - 本说明文档

## 构建特点

✅ **完全自动化** - 一键构建，无需手动配置
✅ **包含所有资源** - 图片、字体、配置文件自动包含
✅ **单文件EXE** - 便于分发
✅ **免费** - GitHub Actions免费额度足够使用
✅ **跨平台兼容** - 构建的EXE可在所有Windows版本运行

## 故障排除

### GitHub Actions构建失败
1. 检查代码是否有语法错误
2. 确认所有依赖都在 `requirements.txt` 中
3. 检查资源文件路径是否正确

### Docker构建失败
1. 确保Docker Desktop正在运行
2. 检查网络连接（需要下载Windows镜像）
3. 确保有足够的磁盘空间

### EXE文件运行失败
1. 在Windows上测试运行
2. 检查是否有缺失的资源文件
3. 查看Windows的错误信息

## 技术细节

- **Python版本**: 3.11 (在Windows环境中)
- **构建工具**: PyInstaller
- **目标平台**: Windows 10/11 64位
- **文件大小**: 约60-80MB（包含所有资源）

## 分发说明

构建好的EXE文件可以：
- 直接发送给Windows用户
- 无需安装Python或其他依赖
- 包含所有必要的资源文件
- 在所有现代Windows系统上运行
