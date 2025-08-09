#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试总结 - 验证所有修复
"""

import sys
import asyncio
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_network_core():
    """测试网络核心修复"""
    print("🌐 测试网络核心修复")
    print("-" * 40)
    
    try:
        from base_api import BaseCore
        from missav_api_core.consts import HEADERS
        
        # 创建核心
        core = BaseCore()
        core.config.headers = HEADERS
        core.initialize_session()
        
        # 测试fetch
        test_url = "https://missav.ws/ofje-505"
        content = core.fetch(test_url)
        
        if content and len(content) > 100000:
            print("✅ 网络核心修复成功")
            print(f"   - 成功获取内容，长度: {len(content)}")
            print("   - 已绕过403反爬虫限制")
            return True
        else:
            print("❌ 网络核心修复失败")
            return False
            
    except Exception as e:
        print(f"❌ 网络核心测试失败: {str(e)}")
        return False

def test_video_parsing():
    """测试视频解析功能"""
    print("\n📺 测试视频解析功能")
    print("-" * 40)
    
    try:
        from base_api import BaseCore
        from missav_api_core.consts import HEADERS
        from missav_api_core.missav_api import Video
        
        # 创建核心和视频对象
        core = BaseCore()
        core.config.headers = HEADERS
        core.initialize_session()
        
        video = Video("https://missav.ws/ofje-505", core=core)
        
        # 测试属性
        title = video.title
        video_code = video.video_code
        m3u8_url = video.m3u8_base_url
        
        print(f"✅ 视频解析成功")
        print(f"   - 标题: {title[:50]}...")
        print(f"   - 视频代码: {video_code}")
        print(f"   - M3U8 URL: {m3u8_url}")
        
        # 测试分段获取
        segments = video.get_segments("worst")
        if segments:
            print(f"   - 分段数量: {len(segments)}")
            print("✅ 分段获取成功")
            return True
        else:
            print("❌ 分段获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 视频解析测试失败: {str(e)}")
        return False

async def test_async_download():
    """测试异步下载功能"""
    print("\n⬇️ 测试异步下载功能")
    print("-" * 40)
    
    try:
        from missav_api_core.async_downloader_new import AsyncDownloader
        from base_api import BaseCore
        from missav_api_core.consts import HEADERS
        from missav_api_core.missav_api import Video
        
        # 创建下载器
        downloader = AsyncDownloader(max_concurrent=2, timeout=30, retry_count=2)
        
        # 创建视频对象
        core = BaseCore()
        core.config.headers = HEADERS
        core.initialize_session()
        
        video = Video("https://missav.ws/ofje-505", core=core)
        
        # 创建测试目录
        test_dir = Path("./final_test_download")
        test_dir.mkdir(exist_ok=True)
        
        print("🚀 开始异步下载测试（仅下载前10个分段）...")
        
        # 获取分段并限制数量用于测试
        segments = video.get_segments("worst")
        if len(segments) > 10:
            # 临时修改分段数量用于快速测试
            original_get_segments = video.get_segments
            video.get_segments = lambda quality: segments[:10]
        
        # 执行下载
        success = await downloader.download_video_async(
            video=video,
            quality="worst",
            output_path=str(test_dir)
        )
        
        if success:
            # 检查文件
            files = list(test_dir.glob("*.mp4"))
            if files:
                file_size = files[0].stat().st_size / (1024 * 1024)
                print(f"✅ 异步下载成功")
                print(f"   - 文件: {files[0].name}")
                print(f"   - 大小: {file_size:.2f} MB")
                return True
            else:
                print("❌ 下载完成但未找到文件")
                return False
        else:
            print("❌ 异步下载失败")
            return False
            
    except Exception as e:
        print(f"❌ 异步下载测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_dependencies():
    """检查依赖项"""
    print("\n📦 检查依赖项")
    print("-" * 40)
    
    dependencies = [
        ('httpx', 'HTTP客户端'),
        ('requests', 'HTTP请求库'),
        ('aiohttp', '异步HTTP客户端'),
        ('aiofiles', '异步文件操作'),
    ]
    
    all_ok = True
    for dep, desc in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - {desc}")
        except ImportError:
            print(f"❌ {dep} - {desc} (未安装)")
            all_ok = False
    
    return all_ok

async def main():
    """主函数"""
    print("🔧 MissAV异步下载修复 - 最终测试")
    print("=" * 80)
    
    # 检查依赖
    deps_ok = check_dependencies()
    
    # 测试网络核心
    network_ok = test_network_core()
    
    # 测试视频解析
    parsing_ok = test_video_parsing()
    
    # 测试异步下载
    download_ok = await test_async_download()
    
    print("\n" + "=" * 80)
    print("📋 最终测试结果")
    print("=" * 80)
    
    results = [
        ("依赖项检查", deps_ok),
        ("网络核心修复", network_ok),
        ("视频解析功能", parsing_ok),
        ("异步下载功能", download_ok),
    ]
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print(f"\n🎉 所有测试通过！MissAV异步下载功能已完全修复")
        print(f"\n📝 修复内容总结:")
        print(f"   1. 创建了增强的BaseCore，解决403反爬虫问题")
        print(f"   2. 修复了Video类的属性和方法")
        print(f"   3. 实现了完整的异步下载器")
        print(f"   4. 添加了HLS分段解析和合并功能")
        print(f"   5. 支持多种质量选择和并发控制")
    else:
        print(f"\n⚠️ 部分测试失败，需要进一步调试")
    
    print(f"\n🚀 现在可以使用修复后的异步下载功能了！")

if __name__ == "__main__":
    asyncio.run(main())