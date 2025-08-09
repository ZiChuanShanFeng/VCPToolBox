#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入分析页面内容，查找预览视频的构造逻辑
"""

import sys
import re
import json
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from missav_api_core import MissAVCrawler

def analyze_page_content(url):
    """深入分析页面内容"""
    print(f"🔍 深入分析页面内容: {url}")
    print("=" * 80)
    
    # 获取页面内容
    crawler = MissAVCrawler()
    extractor = crawler.client.info_extractor
    content = extractor.core.fetch(url)
    
    if not content:
        print("❌ 无法获取页面内容")
        return
    
    print(f"✅ 页面内容长度: {len(content)} 字符")
    print("-" * 80)
    
    # 1. 查找cdnUrl函数定义
    print("📥 步骤1: 查找cdnUrl函数定义")
    cdn_patterns = [
        r'function\s+cdnUrl\s*\([^)]*\)\s*{[^}]+}',
        r'cdnUrl\s*:\s*function\s*\([^)]*\)\s*{[^}]+}',
        r'const\s+cdnUrl\s*=\s*[^;]+;',
        r'var\s+cdnUrl\s*=\s*[^;]+;',
        r'let\s+cdnUrl\s*=\s*[^;]+;',
    ]
    
    for i, pattern in enumerate(cdn_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"  CDN模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches:
                clean_match = match.replace('\n', ' ').replace('\r', '')
                if len(clean_match) > 200:
                    clean_match = clean_match[:200] + "..."
                print(f"    - {clean_match}")
            print()
    
    # 2. 查找dvd_id的值
    print("📥 步骤2: 查找dvd_id的值")
    dvd_id_patterns = [
        r'"dvd_id"\s*:\s*"?([^",\s]+)"?',
        r'dvd_id\s*:\s*"?([^",\s]+)"?',
        r'data-dvd-id\s*=\s*["\']([^"\']+)["\']',
        r'var\s+dvd_id\s*=\s*["\']([^"\']+)["\']',
        r'let\s+dvd_id\s*=\s*["\']([^"\']+)["\']',
        r'const\s+dvd_id\s*=\s*["\']([^"\']+)["\']',
    ]
    
    found_dvd_ids = []
    for i, pattern in enumerate(dvd_id_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"  DVD_ID模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:5]:
                print(f"    - {match}")
                if match not in found_dvd_ids:
                    found_dvd_ids.append(match)
            if len(matches) > 5:
                print(f"    ... 还有 {len(matches) - 5} 个")
            print()
    
    # 3. 查找CDN基础URL
    print("📥 步骤3: 查找CDN基础URL")
    cdn_base_patterns = [
        r'https://[^"\s]*doppiocdn[^"\s]*',
        r'https://media[^"\s]*\.net[^"\s]*',
        r'"cdn[^"]*":\s*"([^"]+)"',
        r'baseUrl\s*:\s*["\']([^"\']+)["\']',
        r'cdnBase\s*:\s*["\']([^"\']+)["\']',
    ]
    
    found_cdn_urls = []
    for i, pattern in enumerate(cdn_base_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"  CDN_BASE模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:3]:
                print(f"    - {match}")
                if match not in found_cdn_urls:
                    found_cdn_urls.append(match)
            if len(matches) > 3:
                print(f"    ... 还有 {len(matches) - 3} 个")
            print()
    
    # 4. 查找完整的视频配置对象
    print("📥 步骤4: 查找视频配置对象")
    config_patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
        r'window\.videoData\s*=\s*({.+?});',
        r'var\s+videoConfig\s*=\s*({.+?});',
        r'const\s+videoConfig\s*=\s*({.+?});',
        r'data:\s*({[^}]*dvd_id[^}]*})',
    ]
    
    for i, pattern in enumerate(config_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"  CONFIG模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:1]:  # 只显示第一个，因为可能很长
                try:
                    # 尝试解析JSON
                    if match.strip().startswith('{'):
                        config_data = json.loads(match)
                        print(f"    - 成功解析JSON配置，包含 {len(config_data)} 个键")
                        
                        # 查找相关的键
                        relevant_keys = []
                        for key in config_data.keys():
                            if any(keyword in key.lower() for keyword in ['video', 'dvd', 'id', 'preview', 'media']):
                                relevant_keys.append(key)
                        
                        if relevant_keys:
                            print(f"      相关键: {relevant_keys}")
                            for key in relevant_keys[:3]:
                                print(f"        {key}: {config_data[key]}")
                    else:
                        clean_match = match.replace('\n', ' ')[:200] + "..."
                        print(f"    - {clean_match}")
                except json.JSONDecodeError:
                    clean_match = match.replace('\n', ' ')[:200] + "..."
                    print(f"    - {clean_match}")
            print()
    
    # 5. 查找具体的预览视频URL模式
    print("📥 步骤5: 查找具体的预览视频URL")
    
    # 基于找到的信息构造预览视频URL
    if found_dvd_ids and found_cdn_urls:
        print("基于找到的信息构造预览视频URL:")
        for dvd_id in found_dvd_ids[:3]:
            for cdn_url in found_cdn_urls[:2]:
                # 清理CDN URL
                clean_cdn = cdn_url.rstrip('/')
                
                # 构造可能的预览视频URL
                possible_urls = [
                    f"{clean_cdn}/{dvd_id}/preview.mp4",
                    f"{clean_cdn}/b-hls-06/{dvd_id}/{dvd_id}_preview.mp4",
                    f"{clean_cdn}/preview/{dvd_id}.mp4",
                ]
                
                for url in possible_urls:
                    print(f"  - {url}")
        print()
    
    # 6. 查找页面中的实际预览视频元素
    print("📥 步骤6: 查找预览视频HTML元素")
    video_element_patterns = [
        r'<video[^>]*preview[^>]*>',
        r'<[^>]*data-src[^>]*preview[^>]*>',
        r'<[^>]*onmouseover[^>]*video[^>]*>',
        r'<[^>]*hover[^>]*video[^>]*>',
    ]
    
    for i, pattern in enumerate(video_element_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"  VIDEO元素模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:2]:
                clean_match = match.replace('\n', ' ')
                if len(clean_match) > 150:
                    clean_match = clean_match[:150] + "..."
                print(f"    - {clean_match}")
            print()
    
    return found_dvd_ids, found_cdn_urls

def test_constructed_urls(dvd_ids, cdn_urls):
    """测试构造的预览视频URL"""
    print("\n📥 测试构造的预览视频URL")
    print("-" * 80)
    
    import requests
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://missav.ws/',
        'Accept': 'video/mp4,video/*,*/*;q=0.9',
    }
    
    test_count = 0
    success_count = 0
    
    for dvd_id in dvd_ids[:2]:  # 只测试前2个ID
        for cdn_url in cdn_urls[:2]:  # 只测试前2个CDN
            clean_cdn = cdn_url.rstrip('/')
            
            test_urls = [
                f"{clean_cdn}/{dvd_id}/preview.mp4",
                f"{clean_cdn}/b-hls-06/{dvd_id}/{dvd_id}_preview.mp4",
                f"{clean_cdn}/preview/{dvd_id}.mp4",
            ]
            
            for test_url in test_urls:
                if test_count >= 10:  # 限制测试数量
                    break
                
                test_count += 1
                print(f"测试 {test_count}: {test_url}")
                
                try:
                    response = requests.head(test_url, headers=headers, timeout=10)
                    print(f"  状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        content_length = response.headers.get('Content-Length', '')
                        print(f"  内容类型: {content_type}")
                        if content_length:
                            print(f"  文件大小: {content_length} 字节")
                        print("  ✅ 成功找到预览视频!")
                        success_count += 1
                    elif response.status_code == 403:
                        print("  ⚠️  403 Forbidden - 可能需要特殊的认证或Referer")
                    else:
                        print("  ❌ 不可访问")
                        
                except Exception as e:
                    print(f"  ❌ 请求失败: {str(e)}")
                
                print()
    
    print(f"测试总结: {success_count}/{test_count} 个URL可访问")

def main():
    """主函数"""
    print("🚀 深入分析页面内容，查找预览视频构造逻辑")
    print("=" * 80)
    
    # 测试URL
    test_url = "https://missav.ws/dm44/jul-875"
    
    # 分析页面内容
    dvd_ids, cdn_urls = analyze_page_content(test_url)
    
    # 测试构造的URL
    if dvd_ids and cdn_urls:
        test_constructed_urls(dvd_ids, cdn_urls)
    
    print("\n" + "=" * 80)
    print("📋 分析完成")
    print(f"找到 {len(dvd_ids)} 个DVD ID")
    print(f"找到 {len(cdn_urls)} 个CDN URL")

if __name__ == "__main__":
    main()