#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接在页面内容中搜索cdnUrl
"""

import sys
import re
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from missav_api_core import MissAVCrawler

def search_cdnurl_in_page(url):
    """直接在页面内容中搜索cdnUrl"""
    print(f"🔍 在页面内容中搜索cdnUrl: {url}")
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
    
    # 搜索cdnUrl的所有出现
    print("📥 搜索cdnUrl的所有出现:")
    
    # 使用不同的搜索模式
    search_patterns = [
        r'cdnUrl',
        r'cdn_url',
        r'cdnURL',
        r'[Cc]dn[Uu]rl',
    ]
    
    all_matches = []
    
    for pattern in search_patterns:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches:
            print(f"模式 '{pattern}': 找到 {len(matches)} 个匹配")
            all_matches.extend(matches)
    
    # 去重并按位置排序
    unique_positions = set()
    unique_matches = []
    
    for match in all_matches:
        if match.start() not in unique_positions:
            unique_positions.add(match.start())
            unique_matches.append(match)
    
    unique_matches.sort(key=lambda x: x.start())
    
    print(f"\n总共找到 {len(unique_matches)} 个唯一的cdnUrl匹配")
    
    # 显示每个匹配及其上下文
    for i, match in enumerate(unique_matches, 1):
        start_pos = match.start()
        end_pos = match.end()
        
        # 获取上下文（前后各100个字符）
        context_start = max(0, start_pos - 100)
        context_end = min(len(content), end_pos + 100)
        
        context = content[context_start:context_end]
        
        # 清理上下文，移除换行符
        clean_context = context.replace('\n', ' ').replace('\r', ' ')
        
        print(f"\n匹配 {i} (位置 {start_pos}-{end_pos}):")
        print(f"  上下文: ...{clean_context}...")
        
        # 尝试提取更大的上下文来找到函数定义
        if 'function' in context.lower() or '=>' in context or '=' in context:
            # 扩展上下文来查找完整的函数定义
            extended_start = max(0, start_pos - 500)
            extended_end = min(len(content), end_pos + 500)
            extended_context = content[extended_start:extended_end]
            
            # 查找函数定义模式
            function_patterns = [
                r'function\s+[^(]*cdnUrl[^(]*\([^)]*\)\s*{[^}]*}',
                r'[^=]*cdnUrl[^=]*=\s*function[^{]*{[^}]*}',
                r'[^=]*cdnUrl[^=]*=\s*[^;]+',
                r'const\s+[^=]*cdnUrl[^=]*=\s*[^;]+',
                r'var\s+[^=]*cdnUrl[^=]*=\s*[^;]+',
                r'let\s+[^=]*cdnUrl[^=]*=\s*[^;]+',
            ]
            
            for pattern in function_patterns:
                func_matches = re.findall(pattern, extended_context, re.IGNORECASE | re.DOTALL)
                if func_matches:
                    print(f"  可能的函数定义:")
                    for func_match in func_matches:
                        clean_func = func_match.replace('\n', ' ').replace('\r', '')
                        if len(clean_func) > 200:
                            clean_func = clean_func[:200] + "..."
                        print(f"    {clean_func}")
    
    # 特别查找Alpine.js的数据绑定
    print(f"\n📥 查找Alpine.js数据绑定中的cdnUrl:")
    
    # 查找x-data属性中的cdnUrl
    alpine_pattern = r'x-data\s*=\s*["\'][^"\']*cdnUrl[^"\']*["\']'
    alpine_matches = re.findall(alpine_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if alpine_matches:
        print(f"找到 {len(alpine_matches)} 个Alpine.js数据绑定:")
        for match in alpine_matches:
            clean_match = match.replace('\n', ' ')
            print(f"  - {clean_match}")
    
    # 查找:data-src属性中的cdnUrl
    data_src_pattern = r':data-src\s*=\s*["\'][^"\']*cdnUrl[^"\']*["\']'
    data_src_matches = re.findall(data_src_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if data_src_matches:
        print(f"找到 {len(data_src_matches)} 个:data-src绑定:")
        for match in data_src_matches:
            clean_match = match.replace('\n', ' ')
            print(f"  - {clean_match}")
    
    # 查找模板字符串中的cdnUrl
    template_pattern = r'`[^`]*cdnUrl[^`]*`'
    template_matches = re.findall(template_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if template_matches:
        print(f"找到 {len(template_matches)} 个模板字符串:")
        for match in template_matches:
            clean_match = match.replace('\n', ' ')
            print(f"  - {clean_match}")

def main():
    """主函数"""
    print("🚀 直接在页面内容中搜索cdnUrl")
    print("=" * 80)
    
    # 测试URL
    test_url = "https://missav.ws/dm44/jul-875"
    
    # 搜索cdnUrl
    search_cdnurl_in_page(test_url)
    
    print("\n" + "=" * 80)
    print("📋 搜索完成")

if __name__ == "__main__":
    main()