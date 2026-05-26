#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Translator - 选中即翻译工具
macOS 版：鼠标选中文字后自动翻译，浮窗显示结果
"""

import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk


# ============================================================
# 翻译引擎
# ============================================================

class GoogleTranslator:
    """Google 免费翻译接口（无需 API Key）"""

    BASE_URL = "https://translate.googleapis.com/translate_a/single"

    @staticmethod
    def detect_lang(text):
        """检测文本语言"""
        try:
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": "zh-CN",
                "dt": "t",
                "q": text[:500]
            }
            url = f"{GoogleTranslator.BASE_URL}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data[2]  # 源语言代码
        except Exception:
            return "en"

    @staticmethod
    def translate(text, target="zh-CN"):
        """翻译文本"""
        if not text or not text.strip():
            return ""

        try:
            # 检测源语言
            src_lang = GoogleTranslator.detect_lang(text)

            # 如果已经是中文，翻译成英文
            if src_lang and src_lang.startswith("zh"):
                target = "en"

            params = {
                "client": "gtx",
                "sl": src_lang or "auto",
                "tl": target,
                "dt": "t",
                "q": text[:2000]
            }
            url = f"{GoogleTranslator.BASE_URL}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # 提取翻译结果
            result = []
            for sentence in data[0]:
                if sentence[0]:
                    result.append(sentence[0])
            return "".join(result)

        except urllib.error.HTTPError as e:
            return f"[HTTP Error {e.code}]"
        except urllib.error.URLError as e:
            return f"[网络错误: {e.reason}]"
        except Exception as e:
            return f"[翻译失败: {type(e).__name__}]"


# ============================================================
# macOS 选中文本获取
# ============================================================

class MacOSSelection:
    """通过 macOS Accessibility API 获取选中文本"""

    @staticmethod
    def get_selected_text():
        """获取当前选中的文本"""
        # 方法1: 使用 osascript 通过 Accessibility API 获取
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
        end tell
        tell application frontApp
            activate
        end tell
        delay 0.05
        tell application "System Events"
            tell process frontApp
                try
                    set selectedText to value of attribute "AXSelectedText" of window 1
                    if selectedText is not "" then return selectedText
                end try
                try
                    set selectedText to value of attribute "AXSelectedText" of (first element whose focused is true)
                    if selectedText is not "" then return selectedText
                end try
            end tell
        end tell
        return ""
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=3
            )
            text = result.stdout.strip()
            if text:
                return text
        except Exception:
            pass

        # 方法2: 使用 pbpaste 获取剪贴板（备用）
        try:
            # 先模拟 Cmd+C
            subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to keystroke "c" using command down'],
                timeout=1
            )
            time.sleep(0.15)
            result = subprocess.run(
                ["pbpaste"], capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip()
        except Exception:
            return ""

    @staticmethod
    def get_frontmost_app():
        """获取当前最前端的应用名称"""
        try:
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to get name of first application process whose frontmost is true'],
                capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip()
        except Exception:
            return ""


# ============================================================
# 翻译浮窗
# ============================================================

class TranslationPopup:
    """无边框翻译浮窗"""

    def __init__(self):
        self.window = None
        self._queue = queue.Queue()
        self._running = True
        self._last_text = ""
        self._last_result = ""
        self._popup_timer = None
        self._hide_timer = None

    def show(self, text, result):
        """显示翻译结果浮窗"""
        if self._popup_timer:
            self.window.after_cancel(self._popup_timer)
            self._popup_timer = None
        if self._hide_timer:
            self.window.after_cancel(self._hide_timer)
            self._hide_timer = None

        # 更新内容
        self._update_display(text, result)

        # 显示窗口
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

        # 自动隐藏（10秒后）
        self._hide_timer = self.window.after(10000, self._auto_hide)

    def _auto_hide(self):
        """自动隐藏窗口"""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def _update_display(self, text, result):
        """更新显示内容"""
        if not hasattr(self, '_source_label') or not self._source_label.winfo_exists():
            return

        self._source_text.delete(1.0, tk.END)
        self._source_text.insert(1.0, text)
        self._result_text.delete(1.0, tk.END)
        self._result_text.insert(1.0, result)

        # 自动调整窗口大小
        self._adjust_size(text, result)

    def _adjust_size(self, text, result):
        """根据内容调整窗口大小"""
        max_line_len = max(
            max((len(line) for line in text.split('\n')), default=0),
            max((len(line) for line in result.split('\n')), default=0)
        )
        line_count = text.count('\n') + result.count('\n') + 2

        # 估算窗口大小
        width = min(max(max_line_len * 9, 300), 600)
        height = min(max(line_count * 22, 100), 400)

        # 获取鼠标位置，在鼠标附近显示
        try:
            mouse_script = 'tell application "System Events" to get position of mouse'
            result_pos = subprocess.run(
                ["osascript", "-e", mouse_script],
                capture_output=True, text=True, timeout=2
            )
            pos = result_pos.stdout.strip()
            if pos:
                x_str, y_str = pos.split(", ")
                x, y = int(x_str), int(y_str)
                # 在鼠标右下方显示
                x = min(x + 10, 1440 - width - 20)
                y = min(y + 20, 900 - height - 20)
                self.window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            self.window.geometry(f"{width}x{height}+100+100")

    def build_ui(self):
        """构建 UI"""
        self.window = tk.Tk()
        self.window.title("翻译")
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes("-topmost", True)  # 置顶
        self.window.attributes("-alpha", 0.95)  # 半透明

        # 主框架
        main_frame = tk.Frame(self.window, bg="#2d2d2d", padx=8, pady=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题栏（可拖动）
        title_frame = tk.Frame(main_frame, bg="#3d3d3d", height=24)
        title_frame.pack(fill=tk.X, pady=(0, 6))
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame, text="🔤 自动翻译",
            bg="#3d3d3d", fg="#cccccc",
            font=("Helvetica", 10)
        )
        title_label.pack(side=tk.LEFT, padx=6)

        # 关闭按钮
        close_btn = tk.Label(
            title_frame, text="✕",
            bg="#3d3d3d", fg="#888888",
            font=("Helvetica", 10, "bold"),
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=6)
        close_btn.bind("<Button-1>", lambda e: self._quit())

        # 拖动功能
        def start_drag(event):
            self._drag_x = event.x
            self._drag_y = event.y

        def do_drag(event):
            x = self.window.winfo_x() + event.x - self._drag_x
            y = self.window.winfo_y() + event.y - self._drag_y
            self.window.geometry(f"+{x}+{y}")

        title_frame.bind("<Button-1>", start_drag)
        title_frame.bind("<B1-Motion>", do_drag)
        title_label.bind("<Button-1>", start_drag)
        title_label.bind("<B1-Motion>", do_drag)

        # 原文区域
        source_frame = tk.Frame(main_frame, bg="#353535")
        source_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self._source_text = tk.Text(
            source_frame, height=3, wrap=tk.WORD,
            bg="#353535", fg="#e0e0e0",
            font=("Helvetica", 11),
            relief=tk.FLAT, padx=6, pady=4,
            highlightthickness=1, highlightbackground="#555555"
        )
        self._source_text.pack(fill=tk.BOTH, expand=True)
        self._source_text.insert(1.0, "选中文字后自动翻译...")

        # 翻译结果区域
        result_frame = tk.Frame(main_frame, bg="#2d4d3d")
        result_frame.pack(fill=tk.BOTH, expand=True)

        self._result_text = tk.Text(
            result_frame, height=3, wrap=tk.WORD,
            bg="#2d4d3d", fg="#ffffff",
            font=("Helvetica", 12, "bold"),
            relief=tk.FLAT, padx=6, pady=4,
            highlightthickness=1, highlightbackground="#3d6d4d"
        )
        self._result_text.pack(fill=tk.BOTH, expand=True)
        self._result_text.insert(1.0, "等待翻译...")

        # 状态栏
        status_frame = tk.Frame(main_frame, bg="#3d3d3d", height=20)
        status_frame.pack(fill=tk.X, pady=(4, 0))
        status_frame.pack_propagate(False)

        self._status_label = tk.Label(
            status_frame, text="就绪 | 选中文字后按 Ctrl+Shift+T 翻译",
            bg="#3d3d3d", fg="#888888",
            font=("Helvetica", 8)
        )
        self._status_label.pack(side=tk.LEFT, padx=6)

        # 窗口事件
        self.window.protocol("WM_DELETE_WINDOW", self._quit)
        self.window.bind("<Escape>", lambda e: self.window.withdraw())

        # 初始隐藏
        self.window.withdraw()

    def set_status(self, text):
        """设置状态栏文字"""
        if hasattr(self, '_status_label') and self._status_label.winfo_exists():
            self._status_label.config(text=text)

    def _quit(self):
        """退出程序"""
        self._running = False
        if self.window:
            self.window.quit()
            self.window.destroy()

    def run(self):
        """运行 UI 主循环"""
        self.build_ui()
        self.window.mainloop()


# ============================================================
# 主控制器
# ============================================================

class AutoTranslator:
    """自动翻译控制器"""

    def __init__(self):
        self.popup = TranslationPopup()
        self.translator = GoogleTranslator()
        self._last_text = ""
        self._last_translation = ""
        self._monitoring = True
        self._clipboard_history = ""

    def _get_selection(self):
        """获取选中文本"""
        return MacOSSelection.get_selected_text()

    def _translate(self, text):
        """执行翻译"""
        if not text or not text.strip():
            return ""

        # 去除首尾空白
        text = text.strip()

        # 如果和上次一样，直接返回缓存
        if text == self._last_text:
            return self._last_translation

        self._last_text = text
        result = self.translator.translate(text)
        self._last_translation = result
        return result

    def _on_selection_changed(self):
        """选中文本变化时的处理"""
        text = self._get_selection()
        if not text or not text.strip():
            return

        text = text.strip()

        # 忽略太短的内容（少于2个字符）
        if len(text) < 2:
            return

        # 忽略纯数字
        if text.replace(".", "").replace("-", "").replace(",", "").strip().isdigit():
            return

        # 如果和上次一样，跳过
        if text == self._last_text:
            return

        self.popup.set_status(f"翻译中... ({len(text)}字符)")

        # 执行翻译
        result = self._translate(text)

        if result and not result.startswith("["):
            self.popup.show(text, result)
            self.popup.set_status(f"✓ 已翻译 | {len(text)}字 → {len(result)}字")
        else:
            self.popup.set_status(f"⚠ {result}")

    def _monitor_loop(self):
        """监控循环 - 使用剪贴板方式"""
        # 保存当前剪贴板内容
        try:
            script = 'tell application "System Events" to keystroke "c" using command down'
            subprocess.run(["osascript", "-e", script], timeout=1)
            time.sleep(0.1)
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
            self._clipboard_history = result.stdout.strip()
        except Exception:
            pass

        while self._monitoring and self.popup._running:
            try:
                # 获取当前选中文本（通过 Accessibility API）
                text = self._get_selection()

                if text and text.strip():
                    text = text.strip()
                    if (len(text) >= 2 and
                        text != self._last_text and
                        not text.replace(".", "").replace("-", "").replace(",", "").strip().isdigit()):

                        self._last_text = text
                        self.popup.set_status(f"翻译中... ({len(text)}字符)")

                        result = self._translate(text)

                        if result and not result.startswith("["):
                            self.popup.show(text, result)
                            self.popup.set_status(f"✓ 已翻译 | {len(text)}字 → {len(result)}字")
                        else:
                            self.popup.set_status(f"⚠ {result}")

            except Exception as e:
                pass

            time.sleep(0.5)  # 每500ms检查一次

    def start(self):
        """启动翻译工具"""
        print("=" * 50)
        print("  自动翻译工具 v1.0")
        print("  Auto Translator for macOS")
        print("=" * 50)
        print()
        print("  ✨ 功能：选中文字后自动翻译")
        print("  📋 支持：英文 ↔ 中文 双向翻译")
        print()
        print("  ⌨️  快捷键：")
        print("     Esc      - 隐藏翻译窗口")
        print("     Ctrl+C   - 退出程序")
        print()
        print("  ⚠️  首次使用需要授予辅助功能权限：")
        print("     系统设置 → 隐私与安全性 → 辅助功能")
        print("     添加终端/Terminal 或 Python")
        print()

        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()

        # 运行 UI
        self.popup.run()


# ============================================================
# 入口
# ============================================================

def main():
    translator = AutoTranslator()
    translator.start()


if __name__ == "__main__":
    main()
