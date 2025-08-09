#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取页面中的所有JavaScript代码，查找cdnUrl函数
"""

import sys
import re
import json
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from missav_api_core import MissAVCrawler

def extract_all_javascript(url):
    """提取页面中的所有JavaScript代码"""
    print(f"🔍 提取所有JavaScript代码: {url}")
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
    
    # 提取所有script标签内容
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL | re.IGNORECASE)
    
    print(f"找到 {len(scripts)} 个script标签")
    
    # 将所有JavaScript代码合并
    all_js_code = '\n'.join(scripts)
    
    # 保存到文件以便分析
    js_file = Path("extracted_javascript.js")
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(all_js_code)
    
    print(f"✅ JavaScript代码已保存到: {js_file}")
    print(f"✅ 总JavaScript代码长度: {len(all_js_code)} 字符")
    
    # 查找cdnUrl相关的代码
    print("\n📥 查找cdnUrl相关代码:")
    
    # 分行查找
    lines = all_js_code.split('\n')
    cdn_lines = []
    
    for i, line in enumerate(lines, 1):
        if 'cdnurl' in line.lower() or 'cdn_url' in line.lower() or 'cdnUrl' in line:
            clean_line = line.strip()
            if clean_line and len(clean_line) > 5:
                print(f"  行{i}: {clean_line}")
                cdn_lines.append((i, clean_line))
    
    # 查找可能的CDN基础URL定义
    print("\n📥 查找CDN基础URL定义:")
    
    cdn_base_patterns = [
        r'["\']https://[^"\']*doppiocdn[^"\']*["\']',
        r'["\']https://media[^"\']*["\']',
        r'baseUrl\s*[:=]\s*["\'][^"\']+["\']',
        r'mediaUrl\s*[:=]\s*["\'][^"\']+["\']',
        r'MEDIA_BASE\s*[:=]\s*["\'][^"\']+["\']',
    ]
    
    found_bases = set()
    
    for pattern in cdn_base_patterns:
        matches = re.findall(pattern, all_js_code, re.IGNORECASE)
        for match in matches:
            clean_match = match.strip('"\'')
            if 'http' in clean_match:
                found_bases.add(clean_match)
    
    print("找到的CDN基础URL:")
    for base in sorted(found_bases):
        print(f"  - {base}")
    
    # 查找函数定义模式
    print("\n📥 查找函数定义:")
    
    function_patterns = [
        r'function\s+\w*[Cc]dn\w*\s*\([^)]*\)\s*{[^}]*}',
        r'\w*[Cc]dn\w*\s*[:=]\s*function\s*\([^)]*\)\s*{[^}]*}',
        r'\w*[Cc]dn\w*\s*[:=]\s*\([^)]*\)\s*=>\s*[^;]+',
        r'const\s+\w*[Cc]dn\w*\s*=\s*[^;]+',
        r'var\s+\w*[Cc]dn\w*\s*=\s*[^;]+',
        r'let\s+\w*[Cc]dn\w*\s*=\s*[^;]+',
    ]
    
    for i, pattern in enumerate(function_patterns, 1):
        matches = re.findall(pattern, all_js_code, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"函数模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches:
                clean_match = match.replace('\n', ' ').replace('\r', '')
                if len(clean_match) > 150:
                    clean_match = clean_match[:150] + "..."
                print(f"  - {clean_match}")
    
    # 查找Alpine.js的全局数据
    print("\n📥 查找Alpine.js全局数据:")
    
    alpine_patterns = [
        r'Alpine\.data\s*\(\s*["\'][^"\']+["\']\s*,\s*function\s*\(\)\s*{[^}]*return\s*{[^}]*}[^}]*}',
        r'window\.\w+\s*=\s*{[^}]*}',
        r'var\s+\w+\s*=\s*{[^}]*cdnUrl[^}]*}',
    ]
    
    for i, pattern in enumerate(alpine_patterns, 1):
        matches = re.findall(pattern, all_js_code, re.IGNORECASE | re.DOTALL)
        if matches:
            print(f"Alpine模式{i}: 找到 {len(matches)} 个匹配")
            for match in matches[:2]:
                clean_match = match.replace('\n', ' ')
                if len(clean_match) > 200:
                    clean_match = clean_match[:200] + "..."
                print(f"  - {clean_match}")
    
    return cdn_lines, found_bases

def analyze_network_requests():
    """分析可能的网络请求模式"""
    print("\n📥 分析网络请求模式")
    print("-" * 80)
    
    # 基于你提供的示例URL，分析可能的模式
    example_url = "https://media-hls.doppiocdn.net/b-hls-06/117758835/117758835_240p_h264_501_FYTY49jYuOBbckr0_1754223961.mp4"
    
    print(f"示例URL: {example_url}")
    
    # 分析URL模式
    # 格式: https://media-hls.doppiocdn.net/b-hls-06/{numeric_id}/{numeric_id}_{quality}_h264_501_FYTY49jYuOBbckr0_{timestamp}.mp4
    
    # 提取模式
    pattern_match = re.match(r'https://([^/]+)/([^/]+)/(\d+)/(\d+)_(\w+)_(.+)\.mp4', example_url)
    
    if pattern_match:
        domain = pattern_match.group(1)
        path_prefix = pattern_match.group(2)
        numeric_id = pattern_match.group(3)
        quality = pattern_match.group(5)
        suffix = pattern_match.group(6)
        
        print(f"域名: {domain}")
        print(f"路径前缀: {path_prefix}")
        print(f"数字ID: {numeric_id}")
        print(f"质量: {quality}")
        print(f"后缀: {suffix}")
        
        # 对于jul-875，我们需要找到对应的数字ID
        print(f"\n对于jul-875，需要找到对应的数字ID")
        print("可能的预览视频URL模式:")
        
        # 假设预览视频使用相同的域名和路径结构
        possible_patterns = [
            f"https://{domain}/{path_prefix}/{{numeric_id}}/{{numeric_id}}_preview.mp4",
            f"https://{domain}/{path_prefix}/{{numeric_id}}/preview.mp4",
            f"https://{domain}/preview/{{numeric_id}}.mp4",
            f"https://{domain}/{{numeric_id}}/preview.mp4",
        ]
        
        for pattern in possible_patterns:
            print(f"  - {pattern}")
    
    # 尝试一些常见的数字ID
    print(f"\n尝试一些可能的数字ID:")
    
    # 这些可能是jul-875对应的数字ID
    possible_ids = [
        "875",
        "000875",
        "0000875",
        "jul875",
        # 可能需要从页面中提取实际的ID
    ]
    
    for pid in possible_ids:
        print(f"  可能ID: {pid}")

def main():
    """主函数"""
    print("🚀 提取所有JavaScript代码，查找cdnUrl函数")
    print("=" * 80)
    
    # 测试URL
    test_url = "https://missav.ws/dm44/jul-875"
    
    # 提取JavaScript代码
    cdn_lines, found_bases = extract_all_javascript(test_url)
    
    # 分析网络请求模式
    analyze_network_requests()
    
    print("\n" + "=" * 80)
    print("📋 提取总结:")
    print(f"找到 {len(cdn_lines)} 行包含cdnUrl的代码")
    print(f"找到 {len(found_bases)} 个CDN基础URL")
    
    if cdn_lines:
        print("\ncdnUrl相关代码行:")
        for line_num, line in cdn_lines[:5]:
            print(f"  行{line_num}: {line}")
    
    print("\n💡 下一步建议:")
    print("1. 检查extracted_javascript.js文件，手动查找cdnUrl函数定义")
    print("2. 可能需要从页面的数据中提取实际的数字ID")
    print("3. 尝试使用浏览器开发者工具查看网络请求")
    print("4. 分析Alpine.js的数据绑定逻辑")

if __name__ == "__main__":
    main()