# GitHub推送指南

## 📋 完整步骤

### 1. 在GitHub上创建仓库
1. 访问 https://github.com/new
2. 仓库名称: `psychology-experiment` (或你喜欢的名字)
3. 保持公开或设为私有
4. **不要**勾选"Add a README file"等选项
5. 点击"Create repository"

### 2. 获取仓库地址
创建后，在仓库页面复制地址，例如：
```
https://github.com/YOUR_USERNAME/psychology-experiment.git
```

### 3. 在终端中执行命令

#### 设置远程仓库（替换为你的实际地址）
```bash
cd "/Users/tshoiasc/心理学实验/程序_内在or外在"
git remote add origin https://github.com/YOUR_USERNAME/psychology-experiment.git
```

#### 推送代码
```bash
git push -u origin main
```

## 🚨 如果推送失败

### 情况1: 权限问题
如果提示权限错误，可能需要：
1. 使用个人访问令牌 (Personal Access Token)
2. 或使用SSH密钥

### 情况2: 仓库已存在内容
如果提示仓库不为空：
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 情况3: 分支名称问题
如果默认分支不是main：
```bash
git branch -M main
git push -u origin main
```

## ✅ 推送成功后

### 自动构建Windows EXE
推送成功后，GitHub Actions会自动开始构建：
1. 访问你的GitHub仓库
2. 点击 "Actions" 标签
3. 等待构建完成（约5-10分钟）
4. 下载 `windows-exe` 构件中的 `心理学实验程序.exe`

### 后续更新
以后更新代码只需：
```bash
git add .
git commit -m "更新描述"
git push
```

## 🔧 故障排除

### 检查Git状态
```bash
git status
git remote -v
git log --oneline
```

### 如果需要重新设置
```bash
git remote remove origin
git remote add origin YOUR_NEW_REPO_URL
git push -u origin main
```

## 💡 提示

- 确保你在正确的目录: `/Users/tshoiasc/心理学实验/程序_内在or外在`
- 替换 `YOUR_USERNAME` 为你的实际GitHub用户名
- 如果使用SSH，确保SSH密钥已配置

## 📞 需要帮助？

如果遇到问题，请提供具体的错误信息，我会帮你解决！
