#!/usr/bin/env python3
"""
依赖项更新脚本

更新有安全漏洞的依赖项到最新版本
"""
import subprocess
import sys


def run_command(cmd):
    """
    运行命令并返回结果
    """
    try:
        # 安全地执行命令，不使用 shell=True
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        print(f"错误信息: {e.stderr}")
        return None


def update_dependencies():
    """
    更新有安全漏洞的依赖项
    """
    print("开始更新依赖项...")
    
    # 需要更新的依赖项及其目标版本
    dependencies_to_update = [
        "cryptography>=46.0.5",
        "django>=5.0.14",
        "pillow>=12.1.1",
        "pip>=26.0",
        "sqlparse>=0.5.4",
        "urllib3>=2.6.3",
        "wheel>=0.46.2"
    ]
    
    for dep in dependencies_to_update:
        print(f"更新 {dep}...")
        cmd = f"pip install --upgrade {dep}"
        output = run_command(cmd)
        if output:
            print(f"更新成功: {dep}")
        else:
            print(f"更新失败: {dep}")
    
    print("\n依赖项更新完成！")
    print("\n运行安全扫描验证更新结果...")
    
    # 再次运行pip-audit验证更新结果
    cmd = "pip-audit"
    output = run_command(cmd)
    if output:
        print("\n安全扫描结果:")
        print(output)
    else:
        print("安全扫描失败")


if __name__ == "__main__":
    update_dependencies()