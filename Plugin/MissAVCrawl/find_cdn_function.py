#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找cdnUrl函数的实际实现
"""

import sys
import re
import json
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from missav_api_core import MissAVCrawler

def find_cdn_function(url):
    """查找cdnUrl函数的实际实现"""
    print(f"🔍 查找cdnUrl函数实现: {url}")
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
    
    # 1. 查找所有包含"cdn"的JavaScript代码
    print("📥 步骤1: 查找所有包含'cdn'的代码")
    
    # 分割页面内容，查找script标签
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL | re.IGNORECASE)
    
    print(f"找到 {len(scripts)} 个script标签")
    
    cdn_related_code = []
    
    for i, script in enumerate(scripts):
        if 'cdn' in script.lower() or 'doppiocdn' in script.lower():
            print(f"\nScript {i+1} 包含CDN相关代码:")
            # 查找具体的CDN相关行
            lines = script.split('\n')
            for line_num, line in enumerate(lines, 1):
                if 'cdn' in line.lower() or 'doppiocdn' in line.lower():
                    clean_line = line.strip()
                    if clean_line and len(clean_line) > 10:  # 过滤掉太短的行
                        print(f"  行{line_num}: {clean_line}")
                        cdn_related_code.append(clean_line)
    
    print("-" * 80)
    
    # 2. 查找具体的cdnUrl函数定义
    print("📥 步骤2: 查找cdnUrl函数定义")
    
    # 更精确的函数定义模式
    function_patterns = [
        r'function\s+cdnUrl\s*\([^)]*\)\s*{[^}]*}',
        r'cdnUrl\s*:\s*function\s*\([^)]*\)\s*{[^}]*}',
        r'cdnUrl\s*=\s*function\s*\([^)]*\)\s*{[^}]*}',
        r'const\s+cdnUrl\s*=\s*[^;]+',
        r'var\s+cdnUrl\s*=\s*[^;]+',
        r'let\s+cdnUrl\s*=\s*[^;]+',
        # 箭头函数
        r'cdnUrl\s*=\s*\([^)]*\)\s*=>\s*[^;]+',
        r'const\s+cdnUrl\s*=\s*\([^)]*\)\s*=>\s*[^;]+',
    ]
    
    found_functions = []
    
    for i, pattern in enumerate(function_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"函数模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches:
                clean_match = match.replace('\n', ' ').replace('\r', '')
                print(f"  - {clean_match}")
                found_functions.append(clean_match)
            print()
    
    # 3. 查找CDN基础URL的定义
    print("📥 步骤3: 查找CDN基础URL定义")
    
    cdn_base_patterns = [
        r'["\']https://[^"\']*doppiocdn[^"\']*["\']',
        r'["\']https://media[^"\']*\.net[^"\']*["\']',
        r'cdn[^=]*=\s*["\'][^"\']+["\']',
        r'baseUrl[^=]*=\s*["\'][^"\']+["\']',
        r'MEDIA_URL[^=]*=\s*["\'][^"\']+["\']',
    ]
    
    found_cdn_bases = []
    
    for i, pattern in enumerate(cdn_base_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"CDN基础URL模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:5]:
                clean_match = match.strip('"\'')
                print(f"  - {clean_match}")
                if clean_match not in found_cdn_bases:
                    found_cdn_bases.append(clean_match)
            if len(matches) > 5:
                print(f"  ... 还有 {len(matches) - 5} 个")
            print()
    
    # 4. 查找Alpine.js或Vue.js的数据绑定
    print("📥 步骤4: 查找Alpine.js/Vue.js数据绑定")
    
    # 查找x-data或data()定义
    data_patterns = [
        r'x-data\s*=\s*["\'][^"\']*["\']',
        r'x-data\s*=\s*{[^}]*}',
        r'data\(\)\s*{[^}]*return\s*{[^}]*}[^}]*}',
    ]
    
    for i, pattern in enumerate(data_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"数据绑定模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:2]:
                clean_match = match.replace('\n', ' ')
                if len(clean_match) > 200:
                    clean_match = clean_match[:200] + "..."
                print(f"  - {clean_match}")
            print()
    
    # 5. 查找window对象上的全局变量
    print("📥 步骤5: 查找window对象上的全局变量")
    
    window_patterns = [
        r'window\.[^=\s]*[Cc]dn[^=\s]*\s*=\s*[^;]+',
        r'window\.[^=\s]*[Mm]edia[^=\s]*\s*=\s*[^;]+',
        r'window\.[^=\s]*[Bb]ase[^=\s]*\s*=\s*[^;]+',
    ]
    
    for i, pattern in enumerate(window_patterns, 1):
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"Window变量模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches:
                print(f"  - {match}")
            print()
    
    # 6. 尝试从已知信息推断CDN URL构造逻辑
    print("📥 步骤6: 推断CDN URL构造逻辑")
    
    # 基于你提供的示例URL分析
    example_url = "https://media-hls.doppiocdn.net/b-hls-06/117758835/117758835_240p_h264_501_FYTY49jYuOBbckr0_1754223961.mp4"
    print(f"示例URL: {example_url}")
    
    # 分析URL结构
    url_parts = example_url.split('/')
    print("URL结构分析:")
    for i, part in enumerate(url_parts):
        print(f"  {i}: {part}")
    
    # 推断可能的CDN基础URL
    possible_cdn_bases = [
        "https://media-hls.doppiocdn.net",
        "https://media-hls.doppiocdn.net/b-hls-06",
    ]
    
    print("\n可能的CDN基础URL:")
    for base in possible_cdn_bases:
        print(f"  - {base}")
    
    # 构造预览视频URL的可能模式
    dvd_id = "jul-875"
    print(f"\n基于DVD ID '{dvd_id}' 构造预览视频URL:")
    
    for base in possible_cdn_bases:
        preview_urls = [
            f"{base}/{dvd_id}/preview.mp4",
            f"{base}/preview/{dvd_id}.mp4",
        ]
        
        for preview_url in preview_urls:
            print(f"  - {preview_url}")
    
    return found_functions, found_cdn_bases

def test_preview_urls():
    """测试推断的预览视频URL"""
    print("\n📥 测试推断的预览视频URL")
    print("-" * 80)
    
    import requests
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://missav.ws/',
        'Accept': 'video/mp4,video/*,*/*;q=0.9',
        'Origin': 'https://missav.ws',
    }
    
    # 基于分析构造的可能URL
    test_urls = [
        "https://media-hls.doppiocdn.net/jul-875/preview.mp4",
        "https://media-hls.doppiocdn.net/preview/jul-875.mp4",
        "https://media-hls.doppiocdn.net/b-hls-06/jul-875/preview.mp4",
        "https://media-hls.doppiocdn.net/b-hls-06/preview/jul-875.mp4",
    ]
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"测试 {i}: {test_url}")
        
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
                return test_url
            elif response.status_code == 403:
                print("  ⚠️  403 Forbidden")
            elif response.status_code == 404:
                print("  ❌ 404 Not Found")
            else:
                print(f"  ❌ 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 请求失败: {str(e)}")
        
        print()
    
    return None

def main():
    """主函数"""
    print("🚀 查找cdnUrl函数的实际实现")
    print("=" * 80)
    
    # 测试URL
    test_url = "https://missav.ws/dm44/jul-875"
    
    # 查找CDN函数
    functions, cdn_bases = find_cdn_function(test_url)
    
    # 测试推断的URL
    success_url = test_preview_urls()
    
    print("\n" + "=" * 80)
    print("📋 查找总结:")
    print(f"找到 {len(functions)} 个可能的cdnUrl函数")
    print(f"找到 {len(cdn_bases)} 个CDN基础URL")
    
    if success_url:
        print(f"✅ 成功找到预览视频URL: {success_url}")
    else:
        print("❌ 未找到可访问的预览视频URL")
    
    print("\n💡 下一步:")
    print("1. 需要分析JavaScript的执行逻辑")
    print("2. 可能需要模拟浏览器环境来执行cdnUrl函数")
    print("3. 或者通过网络抓包来获取实际的预览视频请求")

if __name__ == "__main__":
    main()