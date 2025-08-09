#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 真实热榜爬虫模块
从指定的热榜页面爬取真实数据，结合排序过滤器功能
"""

from typing import Dict, List, Optional
from .sort_filter_module import SortFilterModule
# 移除虚构数据备用源导入
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import sys
import random
from datetime import datetime

from .debug_utils import debug_print


class RealMissAVHotVideos:
    """真实的MissAV热榜爬虫"""
    
    def __init__(self):
        self.base_urls = [
            "https://missav.ws",
            "https://missav.com"
        ]
        
        # 热榜页面URL映射
        self.hot_pages = {
            'en': '/dm22/en',                    # 英文页面
            'chinese_subtitle': '/dm265/chinese-subtitle',  # 中文字幕
            'new': '/dm514/new',                 # 最新
            'release': '/dm588/release',         # 发行
            'uncensored_leak': '/dm621/uncensored-leak',    # 无码流出
            'today_hot': '/dm291/today-hot',     # 今日热门
            'weekly_hot': '/dm169/weekly-hot',   # 每周热门
            'monthly_hot': '/dm257/monthly-hot', # 每月热门
            'siro': '/dm23/siro',               # SIRO系列
            'luxu': '/dm20/luxu',               # LUXU系列
            'gana': '/dm17/gana'                # GANA系列
        }
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_working_base_url(self) -> Optional[str]:
        """获取可用的基础URL"""
        for base_url in self.base_urls:
            try:
                debug_print(f"测试连接: {base_url}")
                response = self.session.get(base_url, timeout=10)
                if response.status_code == 200:
                    debug_print(f"✅ 连接成功: {base_url}")
                    return base_url
            except Exception as e:
                debug_print(f"❌ 连接失败 {base_url}: {str(e)}")
                continue
        return None
    
    def crawl_hot_page(self, page_type: str = 'today_hot', page: int = 1) -> Dict:
        """
        爬取指定热榜页面
        
        Args:
            page_type: 页面类型
            page: 页码
            
        Returns:
            爬取结果
        """
        try:
            # 获取可用的基础URL
            base_url = self.get_working_base_url()
            if not base_url:
                return {
                    "success": False,
                    "error": "无法连接到任何MissAV网站",
                    "results": []
                }
            
            # 构建目标URL
            if page_type not in self.hot_pages:
                page_type = 'today_hot'
            
            page_path = self.hot_pages[page_type]
            target_url = f"{base_url}{page_path}"
            
            # 添加页码参数
            if page > 1:
                separator = '&' if '?' in target_url else '?'
                target_url += f"{separator}page={page}"
            
            debug_print(f"🔍 开始爬取: {target_url}")
            
            # 发送请求
            response = self.session.get(target_url, timeout=15)
            response.raise_for_status()
            
            debug_print(f"✅ 页面获取成功，状态码: {response.status_code}")
            debug_print(f"📄 页面大小: {len(response.content)} bytes")
            
            # 解析页面
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取视频信息
            videos = self.extract_videos_from_soup(soup, base_url)
            
            if not videos:
                debug_print("⚠️ 未找到视频数据，尝试调试页面结构...")
                self.debug_page_structure(soup)
            
            return {
                "success": True,
                "page_type": page_type,
                "page": page,
                "target_url": target_url,
                "results": videos,
                "total_count": len(videos),
                "message": f"成功爬取到 {len(videos)} 个视频",
                "source": "real_crawl"
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"网络请求失败: {str(e)}",
                "results": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"爬取失败: {str(e)}",
                "results": []
            }
    
    def extract_videos_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """从BeautifulSoup对象中提取视频信息"""
        videos = []
        
        # 尝试多种可能的视频容器选择器
        selectors = [
            'div.thumbnail',
            'div.video-item',
            'div.item',
            'article',
            'div[class*="video"]',
            'div[class*="item"]',
            'a[href*="/"]'  # 包含链接的元素
        ]
        
        for selector in selectors:
            video_elements = soup.select(selector)
            debug_print(f"🔍 尝试选择器 '{selector}': 找到 {len(video_elements)} 个元素")
            
            if video_elements:
                for i, element in enumerate(video_elements[:50]):  # 限制处理数量
                    video_info = self.extract_single_video_info(element, base_url)
                    if video_info:
                        videos.append(video_info)
                        if len(videos) >= 30:  # 限制结果数量
                            break
                
                if videos:
                    debug_print(f"✅ 使用选择器 '{selector}' 成功提取到 {len(videos)} 个视频")
                    break
        
        return videos
    
    def extract_single_video_info(self, element, base_url: str) -> Optional[Dict]:
        """从单个元素中提取视频信息"""
        try:
            video_info = {}
            
            # 查找链接
            link_element = element.find('a') if element.name != 'a' else element
            if not link_element or not link_element.get('href'):
                return None
            
            href = link_element.get('href')
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            
            video_info['url'] = href
            
            # 提取视频代码（从URL中）
            video_code_match = re.search(r'/([a-zA-Z0-9]+-[0-9]+)', href, re.IGNORECASE)
            if video_code_match:
                video_info['video_code'] = video_code_match.group(1).upper()
            else:
                # 尝试从alt属性提取
                alt_text = link_element.get('alt', '')
                if alt_text:
                    code_match = re.search(r'([a-zA-Z0-9]+-[0-9]+)', alt_text, re.IGNORECASE)
                    if code_match:
                        video_info['video_code'] = code_match.group(1).upper()
                    else:
                        video_info['video_code'] = alt_text.upper()
                else:
                    video_info['video_code'] = href.split('/')[-1].upper() or 'UNKNOWN'
            
            # 提取标题 - 优先从img的alt属性或链接文本中获取
            title = None
            
            # 1. 尝试从img的alt属性获取完整标题
            img_element = element.find('img')
            if img_element and img_element.get('alt'):
                alt_text = img_element.get('alt').strip()
                if len(alt_text) > 10:  # 确保是完整标题而不是代码
                    title = alt_text
            
            # 2. 尝试从链接文本获取
            if not title:
                link_text = link_element.get_text(strip=True)
                if link_text and len(link_text) > 10:
                    title = link_text
            
            # 3. 尝试从其他元素获取
            if not title:
                title_selectors = [
                    'div.my-2 a',  # 基于观察到的结构
                    '.title', '.video-title', '.name',
                    'h5', 'h4', 'h3', 'h2', 'h1'
                ]
                
                for selector in title_selectors:
                    title_element = element.select_one(selector)
                    if title_element:
                        title_text = title_element.get_text(strip=True)
                        if title_text and len(title_text) > 5:
                            title = title_text
                            break
            
            # 4. 备用方案
            if not title:
                title = link_element.get('alt') or video_info['video_code']
            
            video_info['title'] = title.strip() if title else video_info['video_code']
            
            # 提取缩略图
            if img_element:
                # 优先使用data-src，然后是src
                img_src = img_element.get('data-src') or img_element.get('src')
                if img_src and not img_src.startswith('data:'):  # 排除base64占位符
                    if not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    video_info['thumbnail'] = img_src
            
            # 提取时长 - 查找包含时间格式的span元素
            duration_selectors = [
                'span.absolute.bottom-1.right-1',  # 更精确的选择器
                'span.absolute',  # 基于观察到的结构
                '.duration', '.time', '.length',
                'span[class*="duration"]', 'div[class*="time"]'
            ]
            
            for selector in duration_selectors:
                duration_elements = element.select(selector)
                for duration_element in duration_elements:
                    duration_text = duration_element.get_text(strip=True)
                    # 匹配时间格式：HH:MM:SS 或 MM:SS
                    if re.match(r'\d{1,2}:\d{2}(:\d{2})?', duration_text):
                        video_info['duration'] = duration_text
                        break
                if video_info.get('duration'):
                    break
            
            # 如果没有找到时长，尝试查找所有span元素中的时间格式
            if not video_info.get('duration'):
                all_spans = element.find_all('span')
                for span in all_spans:
                    span_text = span.get_text(strip=True)
                    if re.match(r'\d{1,2}:\d{2}(:\d{2})?', span_text):
                        video_info['duration'] = span_text
                        break
            
            # 提取其他信息
            video_info['publish_date'] = datetime.now().strftime('%Y-%m-%d')
            video_info['source'] = 'real_crawl'
            
            # 验证必要字段
            if video_info.get('video_code') and video_info.get('title'):
                return video_info
            
        except Exception as e:
            debug_print(f"⚠️ 提取视频信息时出错: {str(e)}")
        
        return None
    
    def debug_page_structure(self, soup: BeautifulSoup):
        """调试页面结构"""
        debug_print("\n🔍 调试页面结构:")
        
        # 查找可能包含视频的元素
        potential_containers = [
            'div[class*="video"]',
            'div[class*="item"]', 
            'div[class*="card"]',
            'div[class*="thumb"]',
            'article',
            'section'
        ]
        
        for selector in potential_containers:
            elements = soup.select(selector)
            if elements:
                debug_print(f"  - {selector}: {len(elements)} 个元素")
                if len(elements) > 0:
                    first_element = elements[0]
                    debug_print(f"    第一个元素的类: {first_element.get('class')}")
                    debug_print(f"    第一个元素的文本片段: {first_element.get_text()[:100]}...")
        
        # 查找所有链接
        links = soup.find_all('a', href=True)
        video_links = [link for link in links if re.search(r'/[A-Z0-9]+-[0-9]+', link.get('href', ''))]
        debug_print(f"  - 找到 {len(video_links)} 个可能的视频链接")
        
        if video_links:
            debug_print(f"    示例链接: {video_links[0].get('href')}")


class EnhancedHotVideos:
    """增强的热榜模块"""
    
    def __init__(self):
        self.real_crawler = RealMissAVHotVideos()
        self.sort_filter = SortFilterModule()
        # 移除虚构数据备用源，只使用真实数据
        
        # 分类映射到爬虫页面类型
        self.category_mapping = {
            'daily': 'today_hot',
            'weekly': 'weekly_hot', 
            'monthly': 'monthly_hot',
            'new': 'new',
            'chinese_subtitle': 'chinese_subtitle',
            'uncensored_leak': 'uncensored_leak',
            'siro': 'siro',
            'luxu': 'luxu',
            'gana': 'gana'
        }
    
    def get_hot_videos_with_filters(self, category: str = "daily", page: int = 1,
                                  sort: Optional[str] = None, 
                                  filter_type: Optional[str] = None) -> Dict:
        """
        获取带排序和过滤器的热榜视频
        
        Args:
            category: 热榜分类
            page: 页码
            sort: 排序方式
            filter_type: 过滤器类型
            
        Returns:
            热榜视频结果
        """
        try:
            debug_print(f"🔥 开始获取热榜: category={category}, page={page}, sort={sort}, filter={filter_type}")
            
            # 映射分类到爬虫页面类型
            page_type = self.category_mapping.get(category, 'today_hot')
            
            # 如果有过滤器，优先使用过滤器对应的页面
            if filter_type and filter_type in self.category_mapping:
                page_type = filter_type
            
            # 尝试真实爬虫
            result = self.real_crawler.crawl_hot_page(page_type, page)
            
            if result.get("success") and result.get("results"):
                videos = result.get("results", [])
                
                # 应用客户端排序和过滤
                if filter_type and filter_type not in self.category_mapping:
                    videos = self.sort_filter.apply_client_side_filtering(videos, filter_type)
                
                if sort:
                    videos = self.sort_filter.apply_client_side_sorting(videos, sort)
                
                result["results"] = videos
                result["total_count"] = len(videos)
                result["applied_sort"] = sort
                result["applied_filter"] = filter_type
                result["category"] = category
                
                return result
            
            # 不再使用虚构数据备用源，直接返回失败结果
            debug_print("❌ 真实爬虫失败，不使用虚构数据")
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": "无法从真实数据源获取热榜数据",
                "results": [],
                "total_count": 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": f"获取热榜失败: {str(e)}",
                "results": []
            }
    
    def test_all_hot_pages(self) -> Dict:
        """测试所有热榜页面"""
        results = {}
        
        print("🧪 开始测试所有热榜页面...")
        
        for page_name, page_path in self.real_crawler.hot_pages.items():
            print(f"\n--- 测试 {page_name} ({page_path}) ---")
            
            result = self.real_crawler.crawl_hot_page(page_name, 1)
            
            results[page_name] = {
                "success": result.get("success", False),
                "count": len(result.get("results", [])),
                "error": result.get("error") if not result.get("success") else None,
                "url": result.get("target_url")
            }
            
            if result.get("success"):
                videos = result.get("results", [])
                print(f"✅ 成功: {len(videos)} 个视频")
                if videos:
                    print(f"   示例: {videos[0].get('video_code')} - {videos[0].get('title', '')[:50]}...")
            else:
                print(f"❌ 失败: {result.get('error')}")
            
            # 添加延迟避免请求过快
            time.sleep(random.uniform(1, 3))
        
        return results
    
    def format_response(self, result: Dict) -> str:
        """格式化响应为可读文本"""
        if not result.get("success"):
            error_msg = f"❌ 获取热榜失败: {result.get('error', '未知错误')}"
            if result.get("real_crawl_error"):
                error_msg += f"\n   真实爬虫错误: {result['real_crawl_error']}"
            if result.get("fallback_error"):
                error_msg += f"\n   备用数据源错误: {result['fallback_error']}"
            return error_msg
        
        category = result.get("category", "daily")
        videos = result.get("results", [])
        source = result.get("source", "unknown")
        
        response = f"🔥 MissAV {self._get_category_name(category)} 热榜\n"
        response += f"数据源: {source}\n"
        
        if result.get("target_url"):
            response += f"爬取URL: {result['target_url']}\n"
        
        if result.get("applied_sort"):
            response += f"排序: {self.sort_filter.get_sort_name(result['applied_sort'])}\n"
        
        if result.get("applied_filter"):
            response += f"过滤器: {self.sort_filter.get_filter_name(result['applied_filter'])}\n"
        
        response += f"视频数量: {len(videos)}\n\n"
        
        for i, video in enumerate(videos[:10], 1):  # 显示前10个
            response += f"{i}. {video.get('video_code', 'N/A')} - {video.get('title', 'N/A')[:50]}...\n"
            if video.get('duration'):
                response += f"   时长: {video['duration']}\n"
            response += f"   链接: {video.get('url', 'N/A')}\n"
            if video.get('thumbnail'):
                response += f"   缩略图: {video['thumbnail']}\n"
            response += "\n"
        
        if len(videos) > 10:
            response += f"... 还有 {len(videos) - 10} 个视频\n"
        
        return response
    
    def _get_category_name(self, category: str) -> str:
        """获取分类中文名称"""
        names = {
            "daily": "每日热门",
            "weekly": "每周热门",
            "monthly": "每月热门", 
            "new": "最新",
            "chinese_subtitle": "中文字幕",
            "uncensored_leak": "无码流出",
            "siro": "SIRO系列",
            "luxu": "LUXU系列",
            "gana": "GANA系列"
        }
        return names.get(category, category)


def test_enhanced_hot_videos():
    """测试增强热榜功能"""
    print("🚀 测试增强热榜功能")
    print("=" * 60)
    
    enhanced = EnhancedHotVideos()
    
    # 测试单个页面
    print("\n--- 测试单个热榜页面 ---")
    result = enhanced.get_hot_videos_with_filters("daily", 1)
    print(f"每日热榜: 成功={result.get('success')}, 数量={len(result.get('results', []))}")
    if result.get('success') and result.get('results'):
        video = result['results'][0]
        print(f"示例视频: {video.get('video_code')} - {video.get('title', '')[:50]}...")
    
    # 测试所有页面
    print("\n--- 测试所有热榜页面 ---")
    all_results = enhanced.test_all_hot_pages()
    
    print(f"\n📊 测试结果汇总:")
    success_count = sum(1 for r in all_results.values() if r['success'])
    total_count = len(all_results)
    
    print(f"成功: {success_count}/{total_count} 个页面")
    
    for page_name, info in all_results.items():
        status = "✅" if info["success"] else "❌"
        print(f"{status} {page_name}: {info['count']} 个视频")
        if info.get("error"):
            print(f"    错误: {info['error']}")


if __name__ == "__main__":
    test_enhanced_hot_videos()