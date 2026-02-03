#!/usr/bin/env python3
"""
工具函数模块
"""

import logging
import os
import sys

def setup_logging(level=logging.INFO, log_file=None):
    """设置日志"""
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    # 如果level传入的是int但不是有效的logging级别，使用默认值
    if isinstance(level, int) and level not in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
        level = logging.INFO
    
    if log_file:
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(level=level, format=format_str)
    
    return logging.getLogger(__name__)


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📊 SSCI旅游学术趋势分析系统 v2.0                               ║
║   SSCI Tourism Research Trend Analyzer                           ║
║                                                                  ║
║   功能: 文献计量 | 关键词挖掘 | 研究缺口识别 | AI辅助选题        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印主菜单"""
    menu = """
┌──────────────────────────────────────────────────────────────────┐
│                         📋 主菜单                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. 📂 从OpenAlex获取数据      5. 🧠 LDA主题建模               │
│   2. 📁 导入本地文件            6. 📈 生成可视化图表            │
│   3. 🎲 加载Demo测试数据        7. 🤖 AI辅助分析与选题          │
│   4. 🔑 关键词分析              8. 📋 生成完整报告              │
│                                                                  │
│   9. ❌ 退出程序                                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
    """
    print(menu)


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def safe_input(prompt, default=None):
    """安全的输入函数"""
    try:
        value = input(prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print("\n")
        return default


def ensure_dir(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def format_number(n):
    """格式化数字显示"""
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    elif n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def truncate_text(text, max_len=50):
    """截断文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."
