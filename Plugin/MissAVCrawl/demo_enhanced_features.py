#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 增强功能演示脚本
展示新增的排序、过滤器、增强信息提取和预览视频功能
"""

import sys
import json
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from request_handler import process_request


def demo_enhanced_search():
    """演示增强搜索功能"""
    print("🔍 演示增强搜索功能")
    print("=" * 50)
    
    # 演示1: 基础搜索带排序
    print("\n--- 演示1: 搜索SSIS系列，按总流量排序 ---")
    request = {
        "command": "SearchWithFilters",
        "keyword": "SSIS",
        "sort": "views",
        "max_results": 5
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 搜索成功")
        print(result["result"][:500] + "..." if len(result["result"]) > 500 else result["result"])
    else:
        print(f"❌ 搜索失败: {result['error']}")
    
    # 演示2: 搜索带过滤器
    print("\n--- 演示2: 搜索OFJE系列，中文字幕过滤 ---")
    request = {
        "command": "SearchWithFilters", 
        "keyword": "OFJE",
        "filter": "chinese_subtitle",
        "sort": "saved",
        "max_results": 3
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 过滤搜索成功")
        print(result["result"][:500] + "..." if len(result["result"]) > 500 else result["result"])
    else:
        print(f"❌ 过滤搜索失败: {result['error']}")


def demo_enhanced_hot_videos():
    """演示增强热榜功能"""
    print("\n🔥 演示增强热榜功能")
    print("=" * 50)
    
    # 演示1: 每日热榜带排序
    print("\n--- 演示1: 每日热榜，按收藏数排序 ---")
    request = {
        "command": "GetHotWithFilters",
        "category": "daily",
        "sort": "saved"
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 热榜获取成功")
        print(result["result"][:500] + "..." if len(result["result"]) > 500 else result["result"])
    else:
        print(f"❌ 热榜获取失败: {result['error']}")
    
    # 演示2: 热榜带过滤器
    print("\n--- 演示2: 每周热榜，日本AV过滤 ---")
    request = {
        "command": "GetHotWithFilters",
        "category": "weekly", 
        "filter": "japanese"
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 过滤热榜成功")
        print(result["result"][:500] + "..." if len(result["result"]) > 500 else result["result"])
    else:
        print(f"❌ 过滤热榜失败: {result['error']}")


def demo_enhanced_video_info():
    """演示增强视频信息功能"""
    print("\n🔍 演示增强视频信息功能")
    print("=" * 50)
    
    # 使用一个示例URL
    test_url = "https://missav.ws/ssis-950"
    
    # 演示1: 基础信息获取
    print("\n--- 演示1: 基础视频信息 ---")
    request = {
        "command": "GetVideoInfo",
        "url": test_url
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 基础信息获取成功")
        print(result["result"][:400] + "..." if len(result["result"]) > 400 else result["result"])
    else:
        print(f"❌ 基础信息获取失败: {result['error']}")
    
    # 演示2: 增强信息获取
    print("\n--- 演示2: 增强视频信息 ---")
    request = {
        "command": "GetEnhancedVideoInfo",
        "url": test_url,
        "use_cache": True
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 增强信息获取成功")
        print(result["result"][:600] + "..." if len(result["result"]) > 600 else result["result"])
    else:
        print(f"❌ 增强信息获取失败: {result['error']}")


def demo_preview_videos():
    """演示预览视频功能"""
    print("\n🎬 演示预览视频功能")
    print("=" * 50)
    
    test_url = "https://missav.ws/ssis-950"
    
    # 演示1: 获取预览视频信息
    print("\n--- 演示1: 获取预览视频信息 ---")
    request = {
        "command": "GetPreviewVideos",
        "url": test_url,
        "download": False
    }
    
    result = process_request(request)
    if result["status"] == "success":
        print("✅ 预览视频信息获取成功")
        print(result["result"][:400] + "..." if len(result["result"]) > 400 else result["result"])
    else:
        print(f"❌ 预览视频信息获取失败: {result['error']}")
    
    # 演示2: 下载预览视频（注意：这会实际下载文件）
    print("\n--- 演示2: 下载预览视频（演示模式，不实际下载） ---")
    print("💡 实际使用时的命令格式:")
    print("""
    request = {
        "command": "GetPreviewVideos",
        "url": "https://missav.ws/ssis-950",
        "download": True,
        "video_code": "SSIS-950"
    }
    """)
    print("⚠️  注意：下载预览视频会消耗带宽和存储空间")


def demo_available_options():
    """演示可用的排序和过滤器选项"""
    print("\n📋 可用的排序和过滤器选项")
    print("=" * 50)
    
    print("\n🔄 排序选项:")
    sort_options = {
        'saved': '收藏数',
        'today_views': '日流量',
        'weekly_views': '周流量', 
        'monthly_views': '月流量',
        'views': '总流量',
        'updated': '最近更新',
        'released_at': '发行日期'
    }
    
    for key, name in sort_options.items():
        print(f"  • {key}: {name}")
    
    print("\n🔍 过滤器选项:")
    filter_options = {
        'all': '所有',
        'single': '單人作品',
        'japanese': '日本AV',
        'uncensored_leak': '無碼流出',
        'uncensored': '無碼影片',
        'chinese_subtitle': '中文字幕'
    }
    
    for key, name in filter_options.items():
        print(f"  • {key}: {name}")


def main():
    """主演示函数"""
    print("🚀 MissAV 增强功能演示")
    print("=" * 60)
    print("本演示将展示新增的排序、过滤器、增强信息提取和预览视频功能")
    print("=" * 60)
    
    # 演示各个功能
    demo_available_options()
    demo_enhanced_search()
    demo_enhanced_hot_videos()
    demo_enhanced_video_info()
    demo_preview_videos()
    
    print("\n" + "=" * 60)
    print("✅ 所有功能演示完成")
    print("\n💡 使用提示:")
    print("1. 排序和过滤器可以组合使用，提供更精确的搜索结果")
    print("2. 增强信息提取提供了比基础功能更详细的视频信息")
    print("3. 预览视频功能可以帮助快速预览内容，支持本地缓存")
    print("4. 所有功能都支持智能缓存，提高响应速度")
    print("\n📚 详细使用说明请参考: ENHANCED_FEATURES_GUIDE.md")


if __name__ == "__main__":
    main()