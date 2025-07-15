#!/usr/bin/env python3
"""
WePlus 开发者后台管理系统启动脚本
"""

import os
import sys
import subprocess
import time

def main():
    """主启动函数"""
    # 设置控制台编码为UTF-8
    if os.name == 'nt':  # Windows系统
        os.system('chcp 65001 >nul')
    
    # 显示启动信息
    print("===========================================")
    print("    WePlus 开发者后台管理系统")
    print("===========================================")
    print()
    print("🚀 正在启动管理后台...")
    print("📍 访问地址: http://localhost:9000")
    print("👤 默认账号: admin")
    print("🔑 默认密码: admin123")
    print()
    print("按 Ctrl+C 停止服务")
    print("===========================================")
    print()
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # 启动管理后台
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        print("管理后台已停止")
    except Exception as e:
        print(f"启动失败: {e}")
    finally:
        # 等待用户按键
        input("按任意键退出...")

if __name__ == "__main__":
    main() 