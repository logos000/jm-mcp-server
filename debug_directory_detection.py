#!/usr/bin/env python3
"""
目录检测问题调试脚本
用于分析为什么在Downloads根目录下无法转换PDF，但在子目录下可以
"""

import os
import time
from datetime import datetime

def analyze_directory_structure(base_dir: str, album_id: str = "1201263"):
    """分析目录结构，找出可能的问题"""
    print(f"=== 分析目录结构：{base_dir} ===")
    
    if not os.path.exists(base_dir):
        print(f"❌ 基础目录不存在：{base_dir}")
        return
    
    print(f"✅ 基础目录存在：{base_dir}")
    
    # 列出目录内容
    try:
        entries = os.listdir(base_dir)
        print(f"📁 目录内容数量：{len(entries)}")
        
        # 按类型分类
        dirs = []
        files = []
        
        for entry in entries:
            entry_path = os.path.join(base_dir, entry)
            if os.path.isdir(entry_path):
                dirs.append(entry)
            else:
                files.append(entry)
        
        print(f"📂 子目录数量：{len(dirs)}")
        print(f"📄 文件数量：{len(files)}")
        
        # 显示最近创建的目录
        print("\n🕒 最近创建的目录（按时间排序）：")
        recent_dirs = []
        
        for dir_name in dirs:
            dir_path = os.path.join(base_dir, dir_name)
            try:
                creation_time = os.path.getctime(dir_path)
                modification_time = os.path.getmtime(dir_path)
                recent_dirs.append({
                    'name': dir_name,
                    'path': dir_path,
                    'creation_time': creation_time,
                    'modification_time': modification_time,
                    'age_minutes': (time.time() - creation_time) / 60
                })
            except Exception as e:
                print(f"⚠️ 获取目录时间失败：{dir_name} - {e}")
        
        # 按创建时间排序
        recent_dirs.sort(key=lambda x: x['creation_time'], reverse=True)
        
        for i, dir_info in enumerate(recent_dirs[:10]):  # 显示最新的10个目录
            creation_dt = datetime.fromtimestamp(dir_info['creation_time'])
            age_str = f"{dir_info['age_minutes']:.1f}分钟前"
            print(f"  {i+1}. {dir_info['name']}")
            print(f"     创建时间：{creation_dt.strftime('%Y-%m-%d %H:%M:%S')} ({age_str})")
            
            # 检查是否包含专辑ID
            if album_id in dir_info['name']:
                print(f"     ✅ 包含专辑ID：{album_id}")
            
            # 检查是否是最近创建的（10分钟内）
            if dir_info['age_minutes'] <= 10:
                print(f"     🕒 最近创建（10分钟内）")
            
            print()
        
        # 查找可能的专辑目录
        print("🔍 专辑目录检测：")
        expected_dir = os.path.join(base_dir, album_id)
        
        if os.path.exists(expected_dir):
            print(f"✅ 期望目录存在：{expected_dir}")
            # 检查目录内容
            try:
                album_contents = os.listdir(expected_dir)
                print(f"   内容数量：{len(album_contents)}")
                
                # 检查是否包含图片文件
                image_files = []
                for item in album_contents:
                    item_path = os.path.join(expected_dir, item)
                    if os.path.isfile(item_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                            image_files.append(item)
                
                print(f"   图片文件数量：{len(image_files)}")
                if image_files:
                    print(f"   示例图片：{image_files[:3]}")
                
            except Exception as e:
                print(f"   ❌ 读取目录内容失败：{e}")
        else:
            print(f"❌ 期望目录不存在：{expected_dir}")
            
            # 查找可能匹配的目录
            print("🔍 查找可能的专辑目录：")
            possible_dirs = []
            
            for dir_name in dirs:
                if album_id in dir_name or dir_name in album_id:
                    possible_dirs.append(dir_name)
                    print(f"   ✅ 可能匹配：{dir_name}")
            
            if not possible_dirs:
                print("   ❌ 未找到包含专辑ID的目录")
                
                # 显示最近的几个目录
                print("   📋 最近的目录（可能是下载目录）：")
                for dir_info in recent_dirs[:5]:
                    if dir_info['age_minutes'] <= 60:  # 1小时内
                        print(f"     - {dir_info['name']} ({dir_info['age_minutes']:.1f}分钟前)")
        
    except Exception as e:
        print(f"❌ 分析目录失败：{e}")

def test_directory_detection():
    """测试不同的目录配置"""
    print("=== 目录检测测试 ===\n")
    
    # 测试配置1：Downloads根目录
    print("测试1：Downloads根目录")
    analyze_directory_structure("C:/Users/Cielo/Downloads", "1201263")
    
    print("\n" + "="*60 + "\n")
    
    # 测试配置2：Downloads/Test子目录
    print("测试2：Downloads/Test子目录")
    analyze_directory_structure("C:/Users/Cielo/Downloads/Test", "1201263")

def check_pdf_conversion_requirements(base_dir: str, album_id: str = "1201263"):
    """检查PDF转换的前置条件"""
    print(f"=== PDF转换条件检查：{base_dir} ===")
    
    # 查找专辑目录
    album_dir = os.path.join(base_dir, album_id)
    
    if os.path.exists(album_dir):
        print(f"✅ 专辑目录存在：{album_dir}")
        
        # 检查图片文件
        try:
            contents = os.listdir(album_dir)
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
            image_files = []
            
            for item in contents:
                item_path = os.path.join(album_dir, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in image_extensions:
                        image_files.append(item)
            
            print(f"📷 图片文件数量：{len(image_files)}")
            
            if image_files:
                print("✅ 图片文件检测通过")
                
                # 检查PDF是否已存在
                pdf_path = os.path.join(base_dir, f"{album_id}.pdf")
                if os.path.exists(pdf_path):
                    print(f"📄 PDF已存在：{pdf_path}")
                else:
                    print(f"📄 PDF不存在，可以转换：{pdf_path}")
                
                return True
            else:
                print("❌ 未找到图片文件")
                return False
                
        except Exception as e:
            print(f"❌ 检查图片文件失败：{e}")
            return False
    else:
        print(f"❌ 专辑目录不存在：{album_dir}")
        return False

if __name__ == "__main__":
    print("JM Comic 目录检测调试工具")
    print("=" * 50)
    
    test_directory_detection()
    
    print("\n" + "="*60 + "\n")
    
    print("PDF转换条件检查：")
    print("1. Downloads根目录：")
    check_pdf_conversion_requirements("C:/Users/Cielo/Downloads", "1201263")
    
    print("\n2. Downloads/Test子目录：")
    check_pdf_conversion_requirements("C:/Users/Cielo/Downloads/Test", "1201263")
