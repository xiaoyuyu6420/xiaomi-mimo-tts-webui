"""
跨平台打包脚本 - 将应用打包为独立可执行文件
用法: python build.py
支持: Windows (.exe) / macOS (.app) / Linux (二进制)
"""

import subprocess
import sys
import os
import platform

os.chdir(os.path.dirname(os.path.abspath(__file__)))

system = platform.system()
name = "MiMo-TTS-Voice-Clone"

print("=" * 50)
print(f"  小米 MiMo 语音克隆 - 打包工具")
print(f"  当前平台: {system}")
print("=" * 50)
print()

# 安装依赖
print("[1/2] 安装依赖...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyinstaller"])

# 打包参数
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--name", name,
    "--hidden-import", "pydub",
    "--hidden-import", "pydub.audio_segment",
]

if system == "Windows":
    cmd.append("--noconsole")

cmd.append("app.py")

print(f"[2/2] 正在打包...")
subprocess.check_call(cmd)

# 输出结果
print()
print("=" * 50)
if system == "Windows":
    print(f"  打包完成! 文件: dist/{name}.exe")
elif system == "Darwin":
    print(f"  打包完成! 文件: dist/{name}")
    print()
    print("  如需打包为 DMG:")
    print(f"    hdiutil create -volname '{name}' \\")
    print(f"      -srcfolder dist/{name}.app \\")
    print(f"      -ov -format UDZO dist/{name}.dmg")
    print()
    print("  或使用 create-dmg 工具获得更美观的安装器")
else:
    print(f"  打包完成! 文件: dist/{name}")
    print("  注意: Linux 二进制需要在目标系统上打包才能运行")
print("=" * 50)
