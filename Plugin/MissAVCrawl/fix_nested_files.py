#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复嵌套在错误目录中的视频文件
"""

import shutil
from pathlib import Path

def fix_nested_video_files():
    """修复嵌套在.mp4目录中的视频文件"""
    print("🔧 修复嵌套的视频文件")
    print("=" * 60)
    
    download_dir = Path("Plugin/MissAVCrawl/downloads")
    
    if not download_dir.exists():
        print("❌ 下载目录不存在")
        return
    
    # 查找以.mp4结尾的目录
    mp4_dirs = [item for item in download_dir.iterdir() if item.is_dir() and item.name.endswith('.mp4')]
    
    if not mp4_dirs:
        print("✅ 没有发现需要修复的目录")
        return
    
    print(f"🔍 发现 {len(mp4_dirs)} 个需要修复的目录:")
    
    for mp4_dir in mp4_dirs:
        print(f"\n📁 处理目录: {mp4_dir.name}")
        
        try:
            # 查找目录中的.mp4文件
            video_files = list(mp4_dir.glob("*.mp4"))
            
            if not video_files:
                print("   ❌ 目录中没有找到视频文件")
                continue
            
            for video_file in video_files:
                file_size_mb = video_file.stat().st_size / (1024 * 1024)
                print(f"   📄 找到视频文件: {video_file.name} ({file_size_mb:.2f} MB)")
                
                # 生成新的文件路径（直接在downloads目录下）
                new_file_path = download_dir / video_file.name
                
                # 如果目标文件已存在，生成新名称
                counter = 1
                while new_file_path.exists():
                    name_parts = video_file.stem, counter, video_file.suffix
                    new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    new_file_path = download_dir / new_name
                    counter += 1
                
                print(f"   📤 移动到: {new_file_path.name}")
                
                # 移动文件
                shutil.move(str(video_file), str(new_file_path))
                print(f"   ✅ 文件移动成功")
            
            # 检查目录是否为空，如果为空则删除
            remaining_items = list(mp4_dir.iterdir())
            if not remaining_items:
                mp4_dir.rmdir()
                print(f"   🗑️ 已删除空目录")
            else:
                print(f"   ⚠️ 目录仍包含 {len(remaining_items)} 个项目，未删除")
                
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")

def main():
    """主函数"""
    print("🚀 修复嵌套视频文件")
    print("=" * 80)
    
    fix_nested_video_files()
    
    print("\n" + "=" * 80)
    print("📋 修复完成")
    print("=" * 80)
    
    # 检查修复结果
    download_dir = Path("Plugin/MissAVCrawl/downloads")
    video_files = list(download_dir.glob("*.mp4"))
    mp4_dirs = [item for item in download_dir.iterdir() if item.is_dir() and item.name.endswith('.mp4')]
    
    print(f"✅ 视频文件数: {len(video_files)}")
    print(f"🚫 问题目录数: {len(mp4_dirs)}")
    
    if video_files:
        print("\n📄 视频文件列表:")
        for video_file in video_files:
            size_mb = video_file.stat().st_size / (1024 * 1024)
            print(f"   📄 {video_file.name} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()