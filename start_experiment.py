#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心理学实验启动器
先弹出独立的被试信息录入窗口，然后启动主程序
"""

import os
import sys


def main():
    """主函数：启动被试信息录入窗口"""
    print("=" * 50)
    print("心理学实验程序启动器")
    print("内在与外在驱动：决策权衡实验")
    print("=" * 50)
    
    try:
        # 检查是否存在主程序文件
        if not os.path.exists("main.py"):
            print("错误：未找到主程序文件 main.py")
            input("按任意键退出...")
            return
        
        # 检查是否存在被试信息录入窗口
        if not os.path.exists("participant_info_window.py"):
            print("错误：未找到被试信息录入窗口 participant_info_window.py")
            input("按任意键退出...")
            return
        
        print("正在启动被试信息录入窗口...")
        
        # 导入并运行被试信息录入窗口
        from participant_info_window import main as run_participant_window
        run_participant_window()
        
    except KeyboardInterrupt:
        print("\n用户中断了程序执行")
    except Exception as e:
        print(f"启动过程中发生错误: {e}")
        input("按任意键退出...")


if __name__ == "__main__":
    main()
