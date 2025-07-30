#!/usr/bin/env python3
"""
Android环境测试脚本
用于验证MCP服务器在Android设备上的运行状态
"""

import os
import platform
import tempfile
import shutil
from pathlib import Path

def test_android_environment():
    """测试Android环境兼容性"""
    print("=== Android环境检测 ===")
    
    # 1. 系统信息
    print(f"操作系统: {platform.system()}")
    print(f"平台详情: {platform.platform()}")
    print(f"Python版本: {platform.python_version()}")
    
    # 2. 检测是否为Android
    is_android = 'android' in platform.platform().lower()
    if is_android:
        print("✅ 检测到Android环境")
    else:
        print("ℹ️  非Android环境")
    
    # 3. 存储路径检测
    print("\n=== 存储路径检测 ===")
    android_paths = [
        '/storage/emulated/0/Download',
        '/storage/emulated/0/Downloads', 
        '/sdcard/Download',
        '/sdcard/Downloads',
        '/data/data/com.termux/files/home/downloads',
    ]
    
    available_paths = []
    for path in android_paths:
        if os.path.exists(path):
            try:
                # 测试写入权限
                test_file = os.path.join(path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                available_paths.append(path)
                print(f"✅ {path} - 可读写")
            except:
                print(f"⚠️  {path} - 只读或无权限")
        else:
            print(f"❌ {path} - 不存在")
    
    # 4. 临时目录测试
    print(f"\n=== 临时目录 ===")
    temp_dir = tempfile.gettempdir()
    print(f"临时目录: {temp_dir}")
    
    try:
        test_file = os.path.join(temp_dir, 'test_temp.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ 临时目录可写")
    except Exception as e:
        print(f"❌ 临时目录写入失败: {e}")
    
    # 5. 磁盘空间检查
    print(f"\n=== 磁盘空间检查 ===")
    for path in available_paths:
        try:
            usage = shutil.disk_usage(path)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            print(f"{path}: {free_gb:.1f}GB 可用 / {total_gb:.1f}GB 总计")
        except Exception as e:
            print(f"{path}: 无法获取空间信息 - {e}")
    
    # 6. 推荐配置
    print(f"\n=== 推荐配置 ===")
    if available_paths:
        recommended_path = available_paths[0]
        print(f"推荐存储路径: {recommended_path}")
        
        # 创建JMComic目录
        jm_dir = os.path.join(recommended_path, 'JMComic')
        try:
            os.makedirs(jm_dir, exist_ok=True)
            print(f"✅ 已创建专用目录: {jm_dir}")
        except Exception as e:
            print(f"⚠️  创建目录失败: {e}")
        
        print(f"\n启动命令:")
        print(f"python src/server.py --storage-path {jm_dir}")
    else:
        # 使用临时目录
        fallback_dir = os.path.join(temp_dir, 'jm_comic_downloads')
        os.makedirs(fallback_dir, exist_ok=True)
        print(f"推荐存储路径: {fallback_dir}")
        print(f"\n启动命令:")
        print(f"python src/server.py --storage-path {fallback_dir}")
    
    return available_paths

def test_dependencies():
    """测试依赖包"""
    print(f"\n=== 依赖包检测 ===")
    
    required_packages = [
        'PIL',      # Pillow
        'yaml',     # PyYAML
        'jmcomic',  # JMComic
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包，请安装:")
        print(f"pip install {' '.join(missing_packages)}")
    else:
        print(f"\n✅ 所有依赖包已安装")
    
    return len(missing_packages) == 0

def test_network():
    """测试网络连接"""
    print(f"\n=== 网络连接测试 ===")
    
    import socket
    
    test_hosts = [
        ('google.com', 80),
        ('github.com', 443),
        ('8.8.8.8', 53),
    ]
    
    for host, port in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {host}:{port} - 连通")
            else:
                print(f"❌ {host}:{port} - 无法连接")
        except Exception as e:
            print(f"❌ {host}:{port} - 错误: {e}")

def generate_android_config(storage_path):
    """生成Android优化的配置文件"""
    config = {
        'dir_rule': {
            'base_dir': storage_path
        },
        'client': {
            'download': {
                'retry_times': 5,
                'timeout': 60,
                'concurrent_max': 2,
                'delay_range': [2, 5]
            }
        }
    }
    
    try:
        import yaml
        with open('op_android.yml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"\n✅ 已生成Android配置文件: op_android.yml")
        print(f"使用命令: cp op_android.yml op.yml")
    except Exception as e:
        print(f"\n❌ 生成配置文件失败: {e}")

def main():
    """主测试函数"""
    print("JM Comic MCP服务器 - Android环境测试")
    print("=" * 50)
    
    # 环境检测
    available_paths = test_android_environment()
    
    # 依赖检测
    deps_ok = test_dependencies()
    
    # 网络测试
    test_network()
    
    # 生成配置
    if available_paths:
        recommended_path = os.path.join(available_paths[0], 'JMComic')
        generate_android_config(recommended_path)
    
    # 总结
    print(f"\n" + "=" * 50)
    print("测试总结:")
    
    if available_paths:
        print("✅ 存储路径检测通过")
    else:
        print("⚠️  存储路径受限，将使用临时目录")
    
    if deps_ok:
        print("✅ 依赖包检测通过")
    else:
        print("❌ 需要安装缺失的依赖包")
    
    print(f"\n下一步:")
    if deps_ok and available_paths:
        print("1. 运行: python src/server.py --storage-path <推荐路径>")
        print("2. 配置AI应用连接MCP服务器")
        print("3. 测试下载和PDF转换功能")
    else:
        print("1. 安装缺失的依赖包")
        print("2. 解决存储权限问题")
        print("3. 重新运行此测试脚本")

if __name__ == "__main__":
    main()
