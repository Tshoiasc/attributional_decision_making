#!/usr/bin/env python3
"""
GitHub设置和推送助手
"""

import subprocess
import sys

def run_command(cmd, description=""):
    """运行命令并返回结果"""
    try:
        if description:
            print(f"\n{description}")
        print(f"执行: {cmd}")
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False

def setup_github():
    """设置GitHub远程仓库"""
    print("🚀 GitHub设置和推送助手")
    print("=" * 50)

    # 获取GitHub用户名
    username = input("请输入你的GitHub用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        return

    # 获取仓库名称
    repo_name = input("请输入仓库名称 (默认: psychology-experiment): ").strip()
    if not repo_name:
        repo_name = "psychology-experiment"

    # 构建远程仓库URL
    remote_url = f"https://github.com/{username}/{repo_name}.git"

    print(f"\n📋 配置信息:")
    print(f"用户名: {username}")
    print(f"仓库名: {repo_name}")
    print(f"远程URL: {remote_url}")

    # 确认
    confirm = input(f"\n确认要推送到 {remote_url} 吗? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 操作已取消")
        return

    # 设置远程仓库
    if not run_command(f"git remote add origin {remote_url}", "🔗 添加远程仓库"):
        return

    # 推送代码
    if not run_command("git push -u origin main", "📤 推送代码到GitHub"):
        return

    print("\n✅ 推送成功！")
    print("=" * 50)
    print("🎉 你的代码已经成功推送到GitHub！")
    print(f"访问地址: https://github.com/{username}/{repo_name}")
    print("\n📋 下次推送只需运行:")
    print("  git add .")
    print("  git commit -m '更新描述'")
    print("  git push")

    # 检查GitHub Actions
    print("\n🤖 GitHub Actions状态:")
    print("推送成功后，GitHub会自动开始构建Windows EXE")
    print("查看进度: https://github.com/{username}/{repo_name}/actions")
    print("下载EXE: 在Actions页面找到最新的构建，下载构件")

if __name__ == '__main__':
    setup_github()
