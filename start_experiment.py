#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心理学实验启动器
先弹出独立的被试信息录入窗口，然后启动主程序
"""

import os
import sys

from src.utils.paths import resource_path


def run_main_entry() -> None:
    """直接在当前进程中启动主程序。"""

    from main import main as run_main  # 延迟导入，避免循环依赖

    original_args = sys.argv[:]
    try:
        if "--skip-participant-form" not in sys.argv:
            sys.argv.append("--skip-participant-form")
        if "--run-main" in sys.argv:
            sys.argv.remove("--run-main")
        run_main()
    finally:
        sys.argv[:] = original_args


def run_launcher() -> None:
    """启动被试信息录入窗口。"""

    print("=" * 50)
    print("心理学实验程序启动器")
    print("内在与外在驱动：决策权衡实验")
    print("=" * 50)

    try:
        print("正在启动被试信息录入窗口...")

        from participant_info_window import main as run_participant_window

        run_participant_window()

    except ImportError as exc:
        print(f"错误：无法导入 participant_info_window 模块：{exc}")
        if not getattr(sys, "frozen", False):
            input("按任意键退出...")
    except KeyboardInterrupt:
        print("\n用户中断了程序执行")
    except Exception as exc:
        print(f"启动过程中发生错误: {exc}")
        input("按任意键退出...")


def main() -> None:
    if "--run-main" in sys.argv:
        run_main_entry()
        return
    run_launcher()


if __name__ == "__main__":
    main()
