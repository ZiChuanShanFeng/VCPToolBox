#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新热榜功能演示脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from missav_api_core.enhanced_hot_videos import EnhancedHotVideos


def demo_hot_videos():
    """演示热榜功能"""
    print("🔥 MissAV 新热榜功能演示")
    print("=" * 60)
    
    enhanced = EnhancedHotVideos()
    
    # 演示不同的热榜分类
    demo_cases = [
        ("daily", None, None, "📅 每日热门"),
        ("weekly", None, None, "📊 每周热门"),
        ("monthly", None, None, "📈 每月热门"),
        ("chinese_subtitle", None, None, "🇨🇳 中文字幕"),
        ("uncensored_leak", None, None, "🔓 无码流出"),
        ("new", None, None, "🆕 最新发布"),
        ("siro", None, None, "🎬 SIRO系列"),
        ("luxu", None, None, "💎 LUXU系列"),
        ("gana", None, None, "🌟 GANA系列")
    ]
    
    for category, sort, filter_type, title in demo_cases:
        print(f"\n{title}")
        print("-" * 40)
        
        result = enhanced.get_hot_videos_with_filters(category, 1, sort, filter_type)
        
        if result.get('success'):
            videos = result.get('results', [])
            print(f"✅ 成功获取 {len(videos)} 个视频")
            print(f"🌐 数据源: {result.get('source', 'unknown')}")
            print(f"🔗 爬取URL: {result.get('target_url', 'N/A')}")
            
            # 显示前3个视频
            for i, video in enumerate(videos[:3], 1):
                print(f"\n  {i}. {video.get('video_code', 'N/A')}")
                title_text = video.get('title', 'N/A')
                if len(title_text) > 60:
                    title_text = title_text[:60] + "..."
                print(f"     标题: {title_text}")
                if video.get('duration'):
                    print(f"     时长: {video['duration']}")
                print(f"     链接: {video.get('url', 'N/A')}")
        else:
            print(f"❌ 获取失败: {result.get('error', '未知错误')}")


def demo_with_filters():
    """演示带过滤器和排序的热榜"""
    print(f"\n\n🔧 带过滤器和排序的热榜演示")
    print("=" * 60)
    
    enhanced = EnhancedHotVideos()
    
    # 演示过滤器和排序组合
    filter_demo_cases = [
        ("daily", "views", None, "📅 每日热门 + 按观看量排序"),
        ("weekly", "saved", None, "📊 每周热门 + 按收藏量排序"),
        ("chinese_subtitle", "monthly_views", None, "🇨🇳 中文字幕 + 按月观看量排序"),
        ("daily", None, "chinese_subtitle", "📅 每日热门 + 中文字幕过滤"),
        ("weekly", "views", "uncensored", "📊 每周热门 + 观看量排序 + 无码过滤")
    ]
    
    for category, sort, filter_type, title in filter_demo_cases:
        print(f"\n{title}")
        print("-" * 50)
        
        result = enhanced.get_hot_videos_with_filters(category, 1, sort, filter_type)
        
        if result.get('success'):
            videos = result.get('results', [])
            print(f"✅ 成功获取 {len(videos)} 个视频")
            print(f"🌐 数据源: {result.get('source', 'unknown')}")
            
            if result.get('applied_sort'):
                print(f"🔄 应用排序: {result['applied_sort']}")
            if result.get('applied_filter'):
                print(f"🔍 应用过滤器: {result['applied_filter']}")
            
            # 显示前2个视频
            for i, video in enumerate(videos[:2], 1):
                print(f"\n  {i}. {video.get('video_code', 'N/A')}")
                title_text = video.get('title', 'N/A')
                if len(title_text) > 50:
                    title_text = title_text[:50] + "..."
                print(f"     {title_text}")
                if video.get('duration'):
                    print(f"     时长: {video['duration']}")
        else:
            print(f"❌ 获取失败: {result.get('error', '未知错误')}")


def demo_formatted_response():
    """演示格式化响应"""
    print(f"\n\n📝 格式化响应演示")
    print("=" * 60)
    
    enhanced = EnhancedHotVideos()
    
    # 获取今日热门
    result = enhanced.get_hot_videos_with_filters("daily", 1)
    
    # 使用格式化响应
    formatted_text = enhanced.format_response(result)
    print(formatted_text)


if __name__ == "__main__":
    try:
        # 运行演示
        demo_hot_videos()
        demo_with_filters()
        demo_formatted_response()
        
        print(f"\n\n🎉 演示完成!")
        print("=" * 60)
        print("✨ 新热榜功能特点:")
        print("  • 真实数据爬取，不再是假数据")
        print("  • 支持多种热榜分类")
        print("  • 集成排序和过滤器功能")
        print("  • 自动备用数据源")
        print("  • 完整的视频信息提取")
        print("  • 支持缩略图和时长信息")
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()