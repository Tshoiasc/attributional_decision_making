#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的被试信息录入窗口
在主程序启动前运行，收集被试信息并保存到临时文件
"""

import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional


class ParticipantInfoWindow:
    """被试信息录入窗口（使用tkinter）"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("被试信息录入")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # 居中窗口
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")
        
        self.participant_info: Optional[Dict[str, str]] = None
        
        # 加载配置中的字体设置
        self.font_path = self.load_font_config()
        
        self.setup_ui()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def load_font_config(self) -> str:
        """加载配置文件中的字体设置"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            font_path = config.get("fonts", {}).get("path", "fonts/SimHei.ttf")
            print(f"加载字体配置: {font_path}")
            return font_path
        except Exception as e:
            print(f"加载字体配置失败: {e}, 使用默认字体")
            return "fonts/SimHei.ttf"
    
    def get_font_family(self) -> str:
        """获取字体族名"""
        if self.font_path and "SimHei" in self.font_path:
            return "SimHei"
        elif self.font_path and "YaHei" in self.font_path:
            return "Microsoft YaHei"
        else:
            return "SimHei"  # 默认字体
        
    def setup_ui(self):
        """设置用户界面"""
        font_family = self.get_font_family()
        
        # 主标题
        title_label = tk.Label(
            self.root, 
            text="心理学实验 - 被试信息录入", 
            font=(font_family, 16, "bold"),
            fg="#1a1a1a",
            bg="#f8f9fa"
        )
        title_label.pack(pady=20)
        
        # 设置窗口背景色
        self.root.configure(bg="#f8f9fa")
        
        # 创建表单框架
        form_frame = tk.Frame(self.root, bg="#f8f9fa")
        form_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        # 输入字段
        self.entries = {}
        fields = [
            ("name", "姓名:", True),
            ("age", "年龄:", True),
            ("gender", "性别:", True),
            ("class", "班级:", True)
        ]
        
        for i, (key, label, required) in enumerate(fields):
            # 标签
            label_widget = tk.Label(
                form_frame, 
                text=label, 
                font=(font_family, 11),
                fg="#1a1a1a",
                bg="#f8f9fa"
            )
            label_widget.grid(row=i, column=0, sticky="e", padx=(0, 10), pady=5)
            
            # 输入框或下拉菜单
            if key == "gender":
                entry = ttk.Combobox(
                    form_frame, 
                    values=["男", "女", "其他"], 
                    font=(font_family, 11),
                    width=18,
                    state="readonly"
                )
                entry.set("男")  # 默认值
            else:
                entry = tk.Entry(
                    form_frame, 
                    font=(font_family, 11), 
                    width=20,
                    relief="solid",
                    bd=1,
                    highlightthickness=2,
                    highlightcolor="#2196F3",
                    bg="#ffffff"
                )
            
            entry.grid(row=i, column=1, sticky="w", pady=5)
            self.entries[key] = entry
            
            # 必填标记
            if required:
                required_label = tk.Label(
                    form_frame, 
                    text="*", 
                    fg="#E53E3E", 
                    font=(font_family, 12, "bold"),
                    bg="#f8f9fa"
                )
                required_label.grid(row=i, column=2, sticky="w", padx=(5, 0))
        
        # 按钮框架
        button_frame = tk.Frame(self.root, bg="#f8f9fa")
        button_frame.pack(pady=20)
        
        # 确认按钮
        confirm_btn = tk.Button(
            button_frame,
            text="确认并开始实验",
            font=(font_family, 12, "bold"),
            bg="#4CAF50",
            fg="#000000",
            activebackground="#45a049",
            activeforeground="#000000",
            relief="raised",
            bd=3,
            width=15,
            height=2,
            cursor="hand2",
            command=self.on_confirm
        )
        confirm_btn.pack(side="left", padx=10)
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            font=(font_family, 12, "bold"),
            bg="#f44336",
            fg="#000000",
            activebackground="#da190b",
            activeforeground="#000000",
            relief="raised",
            bd=3,
            width=10,
            height=2,
            cursor="hand2",
            command=self.on_cancel
        )
        cancel_btn.pack(side="left", padx=10)
        
        # 说明文字
        info_label = tk.Label(
            self.root,
            text="请填写完整信息后点击确认开始实验\n标有 * 的字段为必填项",
            font=(font_family, 9),
            fg="#666666",
            bg="#f8f9fa",
            justify="center"
        )
        info_label.pack(pady=10)
        
        # 焦点设置到姓名输入框
        self.entries["name"].focus()
        
        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.on_confirm())
        
    def validate_input(self) -> bool:
        """验证输入"""
        required_fields = ["name", "age", "gender", "class"]
        
        for field in required_fields:
            value = self.entries[field].get().strip()
            if not value:
                messagebox.showerror("输入错误", f"请填写{self.get_field_name(field)}")
                self.entries[field].focus()
                return False
        
        # 验证年龄
        age = self.entries["age"].get().strip()
        try:
            age_int = int(age)
            if age_int < 1 or age_int > 150:
                raise ValueError()
        except ValueError:
            messagebox.showerror("输入错误", "年龄必须是1-150之间的数字")
            self.entries["age"].focus()
            return False
            
        return True
    
    def get_field_name(self, field: str) -> str:
        """获取字段中文名"""
        names = {
            "name": "姓名",
            "age": "年龄", 
            "gender": "性别",
            "class": "班级"
        }
        return names.get(field, field)
    
    def on_confirm(self):
        """确认按钮点击事件"""
        if not self.validate_input():
            return
            
        self.participant_info = {
            "name": self.entries["name"].get().strip(),
            "age": self.entries["age"].get().strip(),
            "gender": self.entries["gender"].get().strip(),
            "class": self.entries["class"].get().strip()
        }
        
        # 保存到临时文件
        try:
            self.save_participant_info()
            # 直接退出，不显示可能卡住的对话框
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("保存错误", f"保存被试信息时出错：{str(e)}")
    
    def on_cancel(self):
        """取消按钮点击事件"""
        if messagebox.askquestion("确认退出", "确定要退出吗？") == "yes":
            self.participant_info = None
            self.root.destroy()
    
    def save_participant_info(self):
        """保存被试信息到临时文件"""
        temp_file = "temp_participant_info.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self.participant_info, f, ensure_ascii=False, indent=2)
        print(f"被试信息已保存到 {temp_file}")
    
    def run(self) -> Optional[Dict[str, str]]:
        """运行窗口并返回被试信息"""
        try:
            self.root.mainloop()
        except tk.TclError:
            # 窗口已被销毁
            pass
        except Exception as e:
            print(f"窗口运行错误: {e}")
        finally:
            # 确保窗口被销毁
            try:
                if self.root.winfo_exists():
                    self.root.destroy()
            except:
                pass
        return self.participant_info


def main():
    """主函数"""
    print("启动被试信息录入窗口...")
    
    try:
        window = ParticipantInfoWindow()
        participant_info = window.run()
        
        if participant_info:
            print("被试信息录入完成:", participant_info)
            
            # 启动主程序
            print("启动心理学实验主程序...")
            import subprocess
            try:
                # 使用非阻塞方式启动主程序
                subprocess.Popen([sys.executable, "main.py", "--skip-participant-form"])
                print("主程序已启动")
            except Exception as e:
                print(f"启动主程序失败: {e}")
                try:
                    root = tk.Tk()
                    root.withdraw()  # 隐藏主窗口
                    messagebox.showerror("启动错误", f"无法启动主程序：{str(e)}")
                    root.destroy()
                except:
                    pass
        else:
            print("用户取消了信息录入")
            
    except Exception as e:
        print(f"运行被试信息录入窗口时出错: {e}")
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showerror("程序错误", f"启动失败：{str(e)}")
            root.destroy()
        except:
            pass


if __name__ == "__main__":
    main()
