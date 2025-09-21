#!/usr/bin/env python3
"""
心理学实验程序打包脚本
用于将Python项目打包成可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False
    return True

def clean_build_files():
    """清理构建文件"""
    print("正在清理构建文件...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # 清理所有__pycache__目录
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                shutil.rmtree(os.path.join(root, dir_name))

def build_exe():
    """使用PyInstaller构建exe"""
    print("正在构建可执行文件...")
    try:
        # 使用spec文件构建
        cmd = [sys.executable, '-m', 'pyinstaller', '--clean', 'build_exe.spec']
        subprocess.check_call(cmd)
        print("构建完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def create_shortcut():
    """创建桌面快捷方式（仅Windows）"""
    if os.name != 'nt':
        return

    try:
        import winshell
        from win32com.client import Dispatch

        exe_name = '心理学实验程序.exe' if os.name == 'nt' else '心理学实验程序'
        exe_path = os.path.join('dist', exe_name)
        desktop = winshell.desktop()

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(os.path.join(desktop, '心理学实验程序.lnk'))
        shortcut.Targetpath = os.path.abspath(exe_path)
        shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(exe_path))
        shortcut.IconLocation = os.path.abspath(exe_path)
        shortcut.save()

        print("桌面快捷方式创建完成")
    except ImportError:
        print("未安装winshell/win32com，无法创建快捷方式")
    except Exception as e:
        print(f"创建快捷方式失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("心理学实验程序打包工具")
    print("=" * 50)

    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误：需要Python 3.7或更高版本")
        return

    # 确认操作
    response = input("这将清理所有构建文件并重新构建exe。继续？(y/N): ")
    if response.lower() != 'y':
        print("操作已取消")
        return

    # 执行构建步骤
    steps = [
        ("清理构建文件", clean_build_files),
        ("安装依赖", install_dependencies),
        ("构建exe", build_exe),
        ("创建快捷方式", create_shortcut),
    ]

    for step_name, step_func in steps:
        print(f"\n执行: {step_name}")
        if not step_func():
            print(f"步骤 '{step_name}' 失败")
            return

    print("\n" + "=" * 50)
    print("打包完成！")
    exe_name = '心理学实验程序.exe' if os.name == 'nt' else '心理学实验程序'
    print(f"可执行文件位于: dist/{exe_name}")

    if os.path.exists('dist'):
        exe_path = os.path.join('dist', exe_name)
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"文件大小: {file_size:.1f} MB")

    print("=" * 50)

if __name__ == '__main__':
    main()