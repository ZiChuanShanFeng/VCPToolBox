#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析多关键词搜索页面的HTML结构
"""

import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from missav_api_core.unified_search_module import UnifiedSearchModule

def analyze_page_structure():
    """分析页面结构差异"""
    print("🔍 分析多关键词搜索页面结构")
    print("=" * 80)
    
    search_module = UnifiedSearchModule()
    
    # 对比两个URL
    urls = {
        "单关键词": "https://missav.ws/search/三上悠亚",
        "多关键词": "https://missav.ws/search/三上悠亚+金发+巨乳+口交"
    }
    
    for name, url in urls.items():
        print(f"\n📋 分析 {name} 搜索页面")
        print(f"URL: {url}")
        print("-" * 60)
        
        try:
            response = search_module.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print(f"页面长度: {len(response.text)}")
            print(f"页面标题: {soup.title.string if soup.title else '无标题'}")
            
            # 分析页面结构
            print("\n🔍 页面结构分析:")
            
            # 1. 查找视频容器
            video_containers = soup.find_all(['div'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['thumbnail', 'video', 'item', 'card', 'grid']
            ))
            print(f"  视频容器数量: {len(video_containers)}")
            
            # 2. 查找所有链接
            all_links = soup.find_all('a', href=True)
            video_links = [link for link in all_links if search_module._is_missav_video_link(link.get('href', ''))]
            print(f"  总链接数量: {len(all_links)}")
            print(f"  视频链接数量: {len(video_links)}")
            
            # 3. 查找特定的class或id
            common_selectors = [
                '.video-list', '.video-grid', '.search-results', '.content',
                '#video-list', '#search-results', '#content',
                '[class*="video"]', '[class*="item"]', '[class*="card"]'
            ]
            
            for selector in common_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"  找到选择器 '{selector}': {len(elements)} 个元素")
            
            # 4. 查找可能的错误信息
            error_indicators = ['no results', '没有结果', '未找到', 'not found', 'empty']
            page_text = soup.get_text().lower()
            for indicator in error_indicators:
                if indicator in page_text:
                    print(f"  ⚠️ 发现可能的错误指示: '{indicator}'")
            
            # 5. 查找JavaScript中的数据
            scripts = soup.find_all('script')
            js_with_data = []
            for script in scripts:
                if script.string and any(keyword in script.string for keyword in ['video', 'data', 'results']):
                    js_with_data.append(script)
            print(f"  包含数据的JS脚本: {len(js_with_data)} 个")
            
            # 6. 显示前几个视频链接（如果有）
            if video_links:
                print(f"\n  前3个视频链接:")
                for i, link in enumerate(video_links[:3], 1):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"    {i}. {href} - {text[:50]}...")
            
            # 7. 检查是否有分页信息
            pagination = soup.find_all(['div', 'nav'], class_=lambda x: x and 'pag' in x.lower())
            if pagination:
                print(f"  分页元素: {len(pagination)} 个")
            
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")
    
    print(f"\n🔍 分析完成！")

if __name__ == "__main__":
    analyze_page_structure()