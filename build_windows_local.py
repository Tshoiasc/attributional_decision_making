#!/usr/bin/env python3
"""
在macOS本地构建Windows EXE的脚本
使用GitHub Actions或本地Docker环境
"""

import os
import subprocess
import sys
from pathlib import Path

def check_docker():
    """检查Docker是否安装"""
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def build_with_docker():
    """使用Docker构建Windows EXE"""
    print("=== 使用Docker构建Windows EXE ===")

    project_root = Path(__file__).parent.absolute()

    # Docker命令
    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{project_root}:/workspace',
        '-w', '/workspace',
        'python:3.11-windowsservercore',
        'powershell.exe', '-Command', '''
            # 安装Python依赖
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            pip install pyinstaller

            # 构建EXE
            pyinstaller --onefile --windowed --name "心理学实验程序" --add-data "config.json;." --add-data "stimuli.csv;." --add-data "fonts;fonts" --add-data "pictures;pictures" main.py

            # 显示结果
            Get-ChildItem dist
        '''
    ]

    try:
        print("正在启动Docker容器构建...")
        subprocess.run(docker_cmd, check=True)
        print("✅ 构建完成！Windows EXE文件位于: dist/心理学实验程序.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker构建失败: {e}")
        return False

def create_github_workflow():
    """创建GitHub Actions工作流"""
    workflow_dir = Path(__file__).parent / '.github' / 'workflows'
    workflow_dir.mkdir(parents=True, exist_ok=True)

    workflow_content = '''name: Build Windows EXE

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Build EXE
      run: |
        pyinstaller --onefile --windowed --name "心理学实验程序" --add-data "config.json;." --add-data "stimuli.csv;." --add-data "fonts;fonts" --add-data "pictures;pictures" main.py

    - name: Upload EXE artifact
      uses: actions/upload-artifact@v4
      with:
        name: windows-exe
        path: dist/心理学实验程序.exe
        retention-days: 30
'''

    workflow_file = workflow_dir / 'build-windows.yml'
    workflow_file.write_text(workflow_content, encoding='utf-8')
    print(f"✅ 已创建GitHub Actions工作流文件: {workflow_file}")

def setup_github_repo():
    """设置GitHub仓库（如果还没有的话）"""
    print("=== 设置GitHub仓库 ===")
    print("1. 在GitHub上创建一个新的仓库")
    print("2. 将你的代码推送到仓库:")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial commit'")
    print("   git branch -M main")
    print("   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
    print("   git push -u origin main")
    print("3. 推送后，GitHub Actions会自动开始构建")

def main():
    """主函数"""
    print("=" * 60)
    print("macOS上构建Windows EXE工具")
    print("=" * 60)

    print("选择构建方法:")
    print("1. 使用GitHub Actions (推荐)")
    print("2. 使用Docker (需要安装Docker)")
    print("3. 查看使用说明")

    choice = input("请选择 (1/2/3): ").strip()

    if choice == '1':
        print("\n=== GitHub Actions方法 ===")
        print("这是在macOS上构建Windows EXE的最简单方法")
        print()

        if not (Path(__file__).parent / '.github' / 'workflows' / 'build-windows.yml').exists():
            create_github_workflow()
        else:
            print("✅ GitHub Actions工作流已存在")

        setup_github_repo()

    elif choice == '2':
        print("\n=== Docker方法 ===")
        if not check_docker():
            print("❌ Docker未安装。请先安装Docker:")
            print("   https://docs.docker.com/desktop/install/mac/")
            return

        build_with_docker()

    elif choice == '3':
        print("\n=== 使用说明 ===")
        print("方法1 - GitHub Actions (推荐):")
        print("  1. 确保代码已推送到GitHub仓库")
        print("  2. 推送代码后，Actions会自动构建")
        print("  3. 在Actions页面下载构建的EXE文件")
        print()
        print("方法2 - Docker:")
        print("  1. 安装Docker Desktop")
        print("  2. 运行此脚本选择选项2")
        print("  3. 等待构建完成")
        print()
        print("构建好的EXE文件将位于 dist/ 目录中")

    else:
        print("❌ 无效选择")

if __name__ == '__main__':
    main()
