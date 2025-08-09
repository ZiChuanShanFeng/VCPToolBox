#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 统一搜索模块
独立封装的搜索功能，供搜索、热榜等功能使用
支持排序参数与过滤器参数的组合使用
"""

import sys
import re
import requests
import time
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, parse_qs
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup

from .debug_utils import debug_print

# 添加当前目录到 Python 路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from consts import HEADERS
from sort_filter_module import SortFilterModule


class UnifiedSearchModule:
    """统一搜索模块"""
    
    def __init__(self):
        self.base_url = "https://missav.ws"
        self.headers = HEADERS.copy()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.sort_filter = SortFilterModule()
        
        # 添加更多的User-Agent轮换和反爬虫措施
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.current_ua_index = 0
        
        # 添加更多反爬虫头部
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def _rotate_user_agent(self):
        """轮换User-Agent"""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        self.session.headers.update({
            'User-Agent': self.user_agents[self.current_ua_index]
        })
    
    def _build_search_url_candidates(self, keyword: str, page: int = 1, 
                                   sort: Optional[str] = None, filter_type: Optional[str] = None) -> List[str]:
        """构建多个候选搜索URL"""
        candidates = []
        
        # 处理关键词编码 - 支持多关键词搜索
        from urllib.parse import quote
        
        # 检测是否是多关键词搜索
        keywords = keyword.strip().split()
        if len(keywords) > 1:
            # 多关键词搜索：优先使用有效的组合方式
            keyword_variants = []
            
            # 1. 如果关键词数量<=3，尝试用+连接（最有效）
            if len(keywords) <= 3:
                keyword_variants.append('+'.join(keywords))
            
            # 2. 尝试前两个关键词用+连接
            if len(keywords) >= 2:
                keyword_variants.append('+'.join(keywords[:2]))
            
            # 3. 只使用第一个关键词作为回退
            keyword_variants.append(keywords[0])
            
            # 4. 原始关键词（空格分隔）作为最后尝试
            keyword_variants.append(keyword.strip())
        else:
            # 单关键词搜索
            keyword_variants = [keyword.strip()]
        
        # 构建查询参数
        params = []
        if page > 1:
            params.append(f"page={page}")
        if sort and sort in self.sort_filter.sort_params:
            sort_value = self.sort_filter.sort_params[sort]
            if sort_value:
                params.append(f"sort={sort_value}")
        if filter_type and filter_type in self.sort_filter.filter_params:
            filter_value = self.sort_filter.filter_params[filter_type]
            if filter_value:
                params.append(f"filters={filter_value}")
        
        param_string = '?' + '&'.join(params) if params else ''
        
        # 为每个关键词变体构建URL
        for variant in keyword_variants:
            encoded_keyword = quote(variant)
            
            # 候选URL格式1: 传统搜索格式
            traditional_url = f"{self.base_url}/search/{encoded_keyword}{param_string}"
            candidates.append(traditional_url)
            
            # 候选URL格式2: 简化搜索格式
            simple_search_url = f"{self.base_url}/{encoded_keyword}{param_string}"
            candidates.append(simple_search_url)
            
            # 候选URL格式3: genres格式（如果有过滤器）
            if filter_type and filter_type != 'all':
                genres_url = f"{self.base_url}/genres/{encoded_keyword}{param_string}"
                candidates.append(genres_url)
        
        # 候选URL格式4: 带dm代码的genres格式（只使用第一个关键词变体）
        first_variant = keyword_variants[0]
        encoded_first = quote(first_variant)
        dm_codes = ["dm4416", "dm54", "dm22"]
        for dm_code in dm_codes:
            for lang in ["zh", "en"]:
                dm_url = f"{self.base_url}/{dm_code}/{lang}/genres/{encoded_first}{param_string}"
                candidates.append(dm_url)
        
        return candidates
    
    def _is_multi_keyword_search(self, keyword: str) -> bool:
        """判断是否是多关键词搜索"""
        keyword = keyword.strip()
        # 检查是否包含空格、+号或逗号分隔的多个关键词
        return (' ' in keyword or '+' in keyword or ',' in keyword) and len(keyword) > 1
    
    def _extract_first_keyword(self, keyword: str) -> str:
        """从多关键词中提取第一个关键词"""
        keyword = keyword.strip()
        # 按不同分隔符分割，取第一个
        if ' ' in keyword:
            return keyword.split()[0]
        elif '+' in keyword:
            return keyword.split('+')[0]
        elif ',' in keyword:
            return keyword.split(',')[0]
        else:
            return keyword
    
    def search_with_filters(self, keyword: str, page: int = 1, 
                           sort: Optional[str] = None, filter_type: Optional[str] = None,
                           max_results: int = 20, max_pages: int = 1, 
                           enhanced_info: bool = False) -> Dict:
        """
        使用排序和过滤器进行搜索
        
        Args:
            keyword: 搜索关键词
            page: 起始页码
            sort: 排序类型
            filter_type: 过滤器类型
            max_results: 每页最大结果数
            max_pages: 最大搜索页数
            enhanced_info: 是否提取增强信息（演员、标签、系列等）
            
        Returns:
            搜索结果字典
        """
        all_results = []
        actual_pages = 0
        
        try:
            for current_page in range(page, page + max_pages):
                # 构建多个候选搜索URL
                url_candidates = self._build_search_url_candidates(keyword, current_page, sort, filter_type)
                
                response = None
                successful_url = None
                
                # 尝试每个候选URL
                for i, search_url in enumerate(url_candidates):
                    debug_print(f"🔍 尝试搜索URL {i+1}/{len(url_candidates)}: {search_url}")
                    
                    # 轮换User-Agent
                    self._rotate_user_agent()
                    
                    # 发送请求，添加重试机制
                    max_retries = 2  # 减少重试次数，因为有多个URL可以尝试
                    success = False
                    
                    for retry in range(max_retries):
                        try:
                            response = self.session.get(search_url, timeout=30)
                            response.raise_for_status()
                            successful_url = search_url
                            success = True
                            debug_print(f"✅ URL {i+1} 请求成功")
                            break
                        except requests.exceptions.HTTPError as e:
                            if e.response.status_code in [403, 404] and retry < max_retries - 1:
                                debug_print(f"⚠️ 遇到{e.response.status_code}错误，等待{1 + retry}秒后重试...")
                                time.sleep(1 + retry)
                                self._rotate_user_agent()
                                continue
                            else:
                                debug_print(f"❌ URL {i+1} 失败: {e.response.status_code}")
                                break
                        except Exception as e:
                            debug_print(f"❌ URL {i+1} 异常: {str(e)}")
                            break
                    
                    if success:
                        break
                
                # 如果所有URL都失败了
                if not response or not successful_url:
                    debug_print(f"❌ 所有搜索URL都失败了")
                    break
                
                # 解析结果
                page_results = self._parse_search_page(response.text, keyword, enhanced_info, max_results)
                
                if page_results:
                    all_results.extend(page_results)
                    actual_pages += 1
                    debug_print(f"✅ 第{current_page}页找到 {len(page_results)} 个结果")
                else:
                    debug_print(f"⚠️ 第{current_page}页没有找到结果")
                    
                    # 如果是多关键词搜索且第一页就没有结果，尝试回退到单关键词搜索
                    if current_page == page and self._is_multi_keyword_search(keyword):
                        debug_print("🔄 多关键词搜索无结果，尝试回退到单关键词搜索")
                        first_keyword = self._extract_first_keyword(keyword)
                        debug_print(f"🔍 使用第一个关键词进行搜索: '{first_keyword}'")
                        
                        # 构建单关键词搜索URL
                        fallback_candidates = self._build_search_url_candidates(first_keyword, current_page, sort, filter_type)
                        
                        # 尝试单关键词搜索
                        for fallback_url in fallback_candidates[:3]:  # 只尝试前3个URL
                            debug_print(f"🔍 尝试回退搜索URL: {fallback_url}")
                            try:
                                fallback_response = self.session.get(fallback_url, timeout=30)
                                fallback_response.raise_for_status()
                                
                                fallback_results = self._parse_search_page(fallback_response.text, first_keyword, enhanced_info, max_results)
                                if fallback_results:
                                    debug_print(f"✅ 回退搜索成功，找到 {len(fallback_results)} 个结果")
                                    all_results.extend(fallback_results)
                                    actual_pages += 1
                                    break
                            except Exception as e:
                                debug_print(f"⚠️ 回退搜索失败: {str(e)}")
                                continue
                    
                    # 如果还是没有结果，停止搜索
                    if not all_results:
                        debug_print("❌ 所有搜索策略都失败，停止搜索")
                        break
                
                # 限制总结果数
                if len(all_results) >= max_results:
                    all_results = all_results[:max_results]
                    break
                
                # 添加延迟避免被封
                if current_page < page + max_pages - 1:
                    time.sleep(1)
            
            # 修复所有结果的封面图片URL
            for video in all_results:
                video_code = video.get("video_code")
                if video_code and (not video.get("thumbnail") or video.get("thumbnail").startswith('data:')):
                    video["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-n.jpg"
            
            # 如果需要增强信息，为每个结果获取详细信息
            debug_print(f"🔍 增强信息参数: enhanced_info={enhanced_info}, 结果数量: {len(all_results)}")
            if enhanced_info and all_results:
                debug_print(f"🔍 开始获取 {len(all_results)} 个视频的增强信息...")
                all_results = self._enrich_video_results(all_results)
            elif enhanced_info and not all_results:
                debug_print("⚠️ 增强信息已启用，但没有搜索结果")
            elif not enhanced_info:
                debug_print("ℹ️ 增强信息未启用，使用基础信息")
            
            return {
                "success": True,
                "keyword": keyword,
                "page": page,
                "sort": sort,
                "filter_type": filter_type,
                "sort_name": self.sort_filter.get_sort_name(sort) if sort else None,
                "filter_name": self.sort_filter.get_filter_name(filter_type) if filter_type else None,
                "results": all_results,
                "total_count": len(all_results),
                "actual_pages": actual_pages,
                "max_pages": max_pages,
                "enhanced_info": enhanced_info,
                "message": f"搜索完成，找到 {len(all_results)} 个结果" + (" (包含增强信息)" if enhanced_info else "")
            }
            
        except Exception as e:
            debug_print(f"❌ 搜索出错: {str(e)}")
            return {
                "success": False,
                "keyword": keyword,
                "page": page,
                "sort": sort,
                "filter_type": filter_type,
                "error": f"搜索失败: {str(e)}",
                "results": [],
                "total_count": 0
            }
    
    def get_hot_videos_with_filters(self, category: str = "daily", page: int = 1,
                                   sort: Optional[str] = None, filter_type: Optional[str] = None,
                                   include_cover: bool = True, include_title: bool = True,
                                   max_results: int = 20, max_pages: int = 1,
                                   enhanced_info: bool = False) -> Dict:
        """
        获取带过滤器的热榜视频 - 与SearchWithFilters看齐
        
        Args:
            category: 热榜类型
            page: 页码
            sort: 排序类型
            filter_type: 过滤器类型
            include_cover: 是否返回视频封面图片URL
            include_title: 是否返回视频完整标题
            max_results: 每页最大结果数量
            max_pages: 最大搜索页数
            enhanced_info: 是否提取增强信息（演员、标签、系列等）
            
        Returns:
            热榜结果字典
        """
        all_results = []
        actual_pages = 0
        
        try:
            for current_page in range(page, page + max_pages):
                # 构建热榜URL
                hot_url = self.sort_filter.build_hot_videos_url(
                    self.base_url, category, current_page, sort, filter_type
                )
                
                debug_print(f"🔥 热榜URL: {hot_url}")
                
                # 轮换User-Agent
                self._rotate_user_agent()
                
                # 发送请求，添加重试机制
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        response = self.session.get(hot_url, timeout=30)
                        response.raise_for_status()
                        break
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 403 and retry < max_retries - 1:
                            debug_print(f"⚠️ 遇到403错误，等待{2 ** retry}秒后重试...")
                            time.sleep(2 ** retry)
                            self._rotate_user_agent()
                            continue
                        else:
                            raise
                
                # 解析结果
                page_results = self._parse_hot_videos_page(response.text, category, enhanced_info, max_results)
                
                if page_results:
                    all_results.extend(page_results)
                    actual_pages += 1
                    debug_print(f"✅ 第{current_page}页找到 {len(page_results)} 个结果")
                else:
                    debug_print(f"⚠️ 第{current_page}页没有找到结果，停止搜索")
                    break
                
                # 限制总结果数
                if len(all_results) >= max_results:
                    all_results = all_results[:max_results]
                    break
                
                # 添加延迟避免被封
                if current_page < page + max_pages - 1:
                    time.sleep(1)
            
            # 修复所有结果的封面图片URL
            for video in all_results:
                video_code = video.get("video_code")
                if video_code and (not video.get("thumbnail") or video.get("thumbnail").startswith('data:')):
                    video["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-n.jpg"
            
            # 如果需要增强信息，为每个结果获取详细信息
            debug_print(f"🔍 增强信息参数: enhanced_info={enhanced_info}, 结果数量: {len(all_results)}")
            if enhanced_info and all_results:
                debug_print(f"🔍 开始获取 {len(all_results)} 个视频的增强信息...")
                all_results = self._enrich_video_results(all_results)
            elif enhanced_info and not all_results:
                debug_print("⚠️ 增强信息已启用，但没有热榜结果")
            elif not enhanced_info:
                debug_print("ℹ️ 增强信息未启用，使用基础信息")
            
            return {
                "success": True,
                "category": category,
                "page": page,
                "sort": sort,
                "filter_type": filter_type,
                "sort_name": self.sort_filter.get_sort_name(sort) if sort else None,
                "filter_name": self.sort_filter.get_filter_name(filter_type) if filter_type else None,
                "results": all_results,
                "total_count": len(all_results),
                "actual_pages": actual_pages,
                "max_pages": max_pages,
                "enhanced_info": enhanced_info,
                "source": "real_crawl",
                "message": f"获取热榜成功，找到 {len(all_results)} 个视频" + (" (包含增强信息)" if enhanced_info else "")
            }
            
        except Exception as e:
            debug_print(f"❌ 获取热榜出错: {str(e)}")
            return {
                "success": False,
                "category": category,
                "page": page,
                "sort": sort,
                "filter_type": filter_type,
                "error": f"获取热榜失败: {str(e)}",
                "results": [],
                "total_count": 0
            }
    
    def _parse_search_page(self, html_content: str, keyword: str, enhanced_info: bool = False, max_results: int = 100) -> List[Dict]:
        """解析搜索结果页面 - 增强版"""
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            debug_print(f"🔍 开始解析搜索页面，页面长度: {len(html_content)}")
            
            # 方法1: 寻找MissAV特定的视频容器
            # MissAV通常使用特定的class名称
            video_containers = soup.find_all(['div'], class_=re.compile(r'.*thumbnail.*|.*video.*|.*item.*|.*card.*|.*grid.*', re.I))
            debug_print(f"🔍 找到 {len(video_containers)} 个可能的视频容器")
            
            seen_codes = set()  # 用于去重
            for container in video_containers:
                video_info = self._extract_video_info_from_container(container, enhanced_info)
                if video_info and self._is_valid_video_info(video_info):
                    # 去重：基于视频代码
                    video_code = video_info.get('video_code', '')
                    if video_code and video_code not in seen_codes:
                        results.append(video_info)
                        seen_codes.add(video_code)
                        debug_print(f"✅ 提取到唯一视频: {video_info.get('title', '无标题')} ({video_code})")
                    elif video_code in seen_codes:
                        debug_print(f"⚠️ 跳过重复视频: {video_code}")
            
            # 方法2: 如果方法1没有结果，尝试寻找所有视频链接
            if not results:
                debug_print("🔍 方法1无结果，尝试方法2：寻找视频链接")
                all_links = soup.find_all('a', href=True)
                debug_print(f"🔍 找到 {len(all_links)} 个链接")
                
                seen_codes = set()  # 用于去重
                for link in all_links:
                    href = link.get('href', '')
                    if self._is_missav_video_link(href):
                        video_info = self._extract_video_info_from_link_enhanced(link)
                        if video_info and self._is_valid_video_info(video_info):
                            # 去重：基于视频代码
                            video_code = video_info.get('video_code', '')
                            if video_code and video_code not in seen_codes:
                                results.append(video_info)
                                seen_codes.add(video_code)
                                debug_print(f"✅ 从链接提取到唯一视频: {video_info.get('title', '无标题')} ({video_code})")
                            elif video_code in seen_codes:
                                debug_print(f"⚠️ 跳过重复视频: {video_code}")
            
            # 方法3: 正则表达式直接提取
            if not results:
                debug_print("🔍 方法2无结果，尝试方法3：正则表达式提取")
                raw_results = self._extract_videos_with_regex(html_content)
                # 验证提取的结果
                for video_info in raw_results:
                    if self._is_valid_video_info(video_info):
                        results.append(video_info)
                        debug_print(f"✅ 正则提取到有效视频: {video_info.get('title', '无标题')} ({video_info.get('video_code', '无代码')})")
                    else:
                        debug_print(f"⚠️ 正则提取到无效视频，已跳过: {video_info.get('title', '无标题')} ({video_info.get('video_code', '无代码')})")
            
            # 方法4: 查找JavaScript中的数据
            if not results:
                debug_print("🔍 方法3无结果，尝试方法4：JavaScript数据提取")
                raw_results = self._extract_videos_from_javascript(html_content)
                # 验证提取的结果
                for video_info in raw_results:
                    if self._is_valid_video_info(video_info):
                        results.append(video_info)
                        debug_print(f"✅ JS提取到有效视频: {video_info.get('title', '无标题')} ({video_info.get('video_code', '无代码')})")
                    else:
                        debug_print(f"⚠️ JS提取到无效视频，已跳过: {video_info.get('title', '无标题')} ({video_info.get('video_code', '无代码')})")
            
            debug_print(f"🎯 最终提取到 {len(results)} 个视频结果")
            
        except Exception as e:
            debug_print(f"❌ 解析搜索页面出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return results[:max_results]  # 根据参数限制结果数量
    
    def _parse_hot_videos_page(self, html_content: str, category: str, enhanced_info: bool = False, max_results: int = 100) -> List[Dict]:
        """解析热榜页面 - 支持增强信息"""
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            debug_print(f"🔍 开始解析热榜页面，页面长度: {len(html_content)}")
            
            # 热榜页面通常有特定的结构
            # 尝试多种解析方法
            
            # 方法1: 寻找热榜特定的容器
            hot_containers = soup.find_all(['div', 'section'], class_=re.compile(r'.*hot.*|.*trend.*|.*popular.*', re.I))
            
            for container in hot_containers:
                video_cards = container.find_all(['div', 'article'], class_=re.compile(r'.*video.*|.*item.*', re.I))
                for card in video_cards:
                    video_info = self._extract_video_info_from_container(card, enhanced_info)
                    if video_info and self._is_valid_video_info(video_info):
                        results.append(video_info)
                        debug_print(f"✅ 提取到热榜视频: {video_info.get('title', '无标题')} ({video_info.get('video_code', '无代码')})")
            
            # 方法2: 如果没有找到热榜容器，使用通用方法
            if not results:
                debug_print("🔍 方法1无结果，尝试通用方法")
                results = self._parse_generic_video_list(soup)
            
            # 方法3: 如果还是没有结果，使用搜索页面的解析方法
            if not results:
                debug_print("🔍 方法2无结果，尝试搜索页面解析方法")
                results = self._parse_search_page(html_content, f"热榜-{category}", enhanced_info, max_results)
            
            debug_print(f"🎯 最终提取到 {len(results)} 个热榜视频结果")
            
        except Exception as e:
            debug_print(f"❌ 解析热榜页面出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return results[:max_results]  # 根据参数限制结果数量
    
    def _extract_video_info_from_container(self, container, extract_enhanced: bool = False) -> Optional[Dict]:
        """从视频容器中提取信息 - 增强版"""
        try:
            video_info = {
                "url": "",
                "video_code": "",
                "title": "",
                "thumbnail": "",
                "duration": "",
                "publish_date": "",
                "views": ""
            }
            
            # 提取链接 - 更全面的搜索
            link = container.find('a', href=True)
            if not link:
                # 尝试在父元素中查找
                parent = container.parent
                if parent:
                    link = parent.find('a', href=True)
            
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                elif not href.startswith('http'):
                    href = urljoin(self.base_url, '/' + href)
                
                if self._is_missav_video_link(href):
                    video_info["url"] = href
                    video_info["video_code"] = self._extract_video_code_from_url(href)
            
            # 提取标题 - 多种方式
            title = ""
            # 方式1: 从标题标签
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # 方式2: 从title属性
            if not title:
                title_attr_elem = container.find(attrs={'title': True})
                if title_attr_elem:
                    title = title_attr_elem.get('title', '').strip()
            
            # 方式3: 从alt属性
            if not title:
                img_with_alt = container.find('img', alt=True)
                if img_with_alt:
                    title = img_with_alt.get('alt', '').strip()
            
            # 方式4: 从链接文本
            if not title and link:
                title = link.get_text(strip=True)
            
            video_info["title"] = title
            
            # 提取缩略图 - 多种方式，优先获取真实图片URL
            img = container.find('img')
            if img:
                # 优先级：data-src > src > data-lazy > data-original
                src = (img.get('data-src') or img.get('src') or 
                      img.get('data-lazy') or img.get('data-original'))
                
                # 过滤掉base64和占位符图片
                if src and not src.startswith('data:') and 'placeholder' not in src.lower():
                    if src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    elif not src.startswith('http'):
                        src = urljoin(self.base_url, '/' + src)
                    video_info["thumbnail"] = src
                else:
                    # 尝试从视频代码构建封面URL
                    if video_info["video_code"]:
                        # MissAV的封面图片通常在fourhoi.com域名下
                        cover_url = f"https://fourhoi.com/{video_info['video_code']}/cover-n.jpg"
                        video_info["thumbnail"] = cover_url
            
            # 提取时长
            duration_patterns = [
                r'\b(\d{1,2}:\d{2}:\d{2})\b',  # HH:MM:SS
                r'\b(\d{1,2}:\d{2})\b'        # MM:SS
            ]
            
            container_text = container.get_text()
            for pattern in duration_patterns:
                duration_match = re.search(pattern, container_text)
                if duration_match:
                    video_info["duration"] = duration_match.group(1)
                    break
            
            # 提取发布日期
            date_patterns = [
                r'\b(\d{4}-\d{2}-\d{2})\b',
                r'\b(\d{2}/\d{2}/\d{4})\b',
                r'\b(\d{4}/\d{2}/\d{2})\b'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, container_text)
                if date_match:
                    video_info["publish_date"] = date_match.group(1)
                    break
            
            # 如果需要增强信息，尝试提取更多详细信息
            if extract_enhanced and video_info["url"]:
                enhanced_info = self._extract_enhanced_info_from_container(container, video_info)
                video_info.update(enhanced_info)
            
            return video_info if video_info["url"] and video_info["video_code"] else None
            
        except Exception as e:
            debug_print(f"❌ 提取视频容器信息出错: {str(e)}")
            return None
    
    def _extract_enhanced_info_from_container(self, container, basic_info: Dict) -> Dict:
        """从容器中提取增强信息"""
        enhanced_info = {}
        
        try:
            container_text = container.get_text()
            
            # 提取演员信息
            actresses = []
            actress_patterns = [
                r'演员[：:]\s*([^，,\n]+)',
                r'女优[：:]\s*([^，,\n]+)',
                r'主演[：:]\s*([^，,\n]+)'
            ]
            
            for pattern in actress_patterns:
                matches = re.findall(pattern, container_text)
                for match in matches:
                    actresses.extend([name.strip() for name in re.split(r'[，,、]', match) if name.strip()])
            
            if actresses:
                enhanced_info["actresses"] = list(set(actresses))
            
            # 提取类型/标签
            tags = []
            tag_patterns = [
                r'类型[：:]\s*([^，,\n]+)',
                r'标签[：:]\s*([^，,\n]+)',
                r'分类[：:]\s*([^，,\n]+)'
            ]
            
            for pattern in tag_patterns:
                matches = re.findall(pattern, container_text)
                for match in matches:
                    tags.extend([tag.strip() for tag in re.split(r'[，,、]', match) if tag.strip()])
            
            if tags:
                enhanced_info["tags"] = list(set(tags))
            
            # 提取系列信息
            series_patterns = [
                r'系列[：:]\s*([^，,\n]+)',
                r'シリーズ[：:]\s*([^，,\n]+)'
            ]
            
            for pattern in series_patterns:
                match = re.search(pattern, container_text)
                if match:
                    enhanced_info["series"] = match.group(1).strip()
                    break
            
            # 提取发行商信息
            studio_patterns = [
                r'发行商[：:]\s*([^，,\n]+)',
                r'制作商[：:]\s*([^，,\n]+)',
                r'スタジオ[：:]\s*([^，,\n]+)'
            ]
            
            for pattern in studio_patterns:
                match = re.search(pattern, container_text)
                if match:
                    enhanced_info["studio"] = match.group(1).strip()
                    break
            
            # 提取观看次数
            views_patterns = [
                r'观看[：:]\s*(\d+)',
                r'播放[：:]\s*(\d+)',
                r'(\d+)\s*次观看'
            ]
            
            for pattern in views_patterns:
                match = re.search(pattern, container_text)
                if match:
                    enhanced_info["view_count"] = match.group(1)
                    break
            
            # 提取评分信息
            rating_patterns = [
                r'评分[：:]\s*(\d+\.?\d*)',
                r'★\s*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*分'
            ]
            
            for pattern in rating_patterns:
                match = re.search(pattern, container_text)
                if match:
                    enhanced_info["rating"] = match.group(1)
                    break
            
        except Exception as e:
            debug_print(f"⚠️ 提取增强信息时出错: {str(e)}")
        
        return enhanced_info
    
    def _enrich_video_results(self, results: List[Dict]) -> List[Dict]:
        """为视频结果添加增强信息"""
        enriched_results = []
        
        for i, video in enumerate(results):
            try:
                debug_print(f"📊 获取第 {i+1}/{len(results)} 个视频的增强信息: {video.get('video_code', '未知')}")
                
                # 尝试从视频页面获取更详细的信息
                enhanced_video = self._get_enhanced_video_info(video)
                enriched_results.append(enhanced_video)
                
                # 添加延迟避免请求过快
                if i < len(results) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                debug_print(f"⚠️ 获取视频 {video.get('video_code', '未知')} 的增强信息失败: {str(e)}")
                # 如果获取增强信息失败，保留原始信息
                enriched_results.append(video)
        
        return enriched_results
    
    def _get_enhanced_video_info(self, basic_video_info: Dict) -> Dict:
        """获取单个视频的增强信息 - 使用与GetEnhancedVideoInfo相同的逻辑"""
        try:
            video_url = basic_video_info.get("url")
            video_code = basic_video_info.get("video_code")
            
            if not video_url or not video_code:
                return basic_video_info
            
            # 构建正确的视频页面URL，确保访问中文页面
            # 移除URL中的 /en 部分以获取中文内容
            if '/en/' in video_url:
                video_url = video_url.replace('/en/', '/')
            elif video_url.endswith('/en'):
                video_url = video_url[:-3]
            
            # 如果URL包含 /dmXX/ 格式，保持原样，因为这可能是正确的路径
            # 只有当URL格式不正确时才使用标准格式
            if not video_url.endswith(video_code) and '/dm' not in video_url:
                video_url = f"{self.base_url}/{video_code}"
            
            # 尝试使用与GetEnhancedVideoInfo相同的方法
            try:
                # 导入并使用相同的信息提取器
                from .missav_api import Client
                api_client = Client()
                
                if hasattr(api_client, 'get_enhanced_video_info'):
                    enhanced_result = api_client.get_enhanced_video_info(video_url, use_cache=False)
                    if enhanced_result.get("success"):
                        # 数据直接在返回结果的根级别，不在info字段中
                        enhanced_data = enhanced_result
                        
                        # 将增强数据合并到基础信息中
                        result = basic_video_info.copy()
                        
                        # 映射字段名（使用API实际返回的字段名）
                        field_mapping = {
                            'title': 'title',  # 添加标题字段映射
                            'actresses': 'actresses',
                            'types': 'tags',  # API中类型字段叫types
                            'tags': 'labels',  # API中标签字段叫tags
                            'publisher': 'studio',  # API中发行商字段叫publisher
                            'duration': 'duration',
                            'release_date': 'release_date',
                            'description': 'description',
                            'available_resolutions': 'available_resolutions',
                            'preview_videos': 'preview_videos',
                            'm3u8_url': 'main_m3u8',  # API中M3U8字段叫m3u8_url
                            'main_preview': 'main_preview'
                        }
                        
                        for api_field, result_field in field_mapping.items():
                            if api_field in enhanced_data and enhanced_data[api_field]:
                                result[result_field] = enhanced_data[api_field]
                        
                        # 处理分辨率信息
                        if 'available_resolutions' in enhanced_data and enhanced_data['available_resolutions']:
                            resolutions = enhanced_data['available_resolutions']
                            if isinstance(resolutions, list):
                                formatted_resolutions = []
                                for res in resolutions:
                                    if isinstance(res, dict) and 'quality' in res and 'resolution' in res:
                                        formatted_resolutions.append({
                                            "quality": res['quality'],
                                            "resolution": res['resolution']
                                        })
                                    elif isinstance(res, str):
                                        formatted_resolutions.append({
                                            "quality": res,
                                            "resolution": "未知"
                                        })
                                
                                result['available_resolutions'] = formatted_resolutions
                                result['resolution_count'] = len(formatted_resolutions)
                        
                        # 确保封面图片URL正确
                        if enhanced_data.get('main_cover'):
                            result["thumbnail"] = enhanced_data['main_cover']
                        elif not result.get("thumbnail") or result.get("thumbnail").startswith('data:'):
                            result["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-n.jpg"
                        
                        return result
            except Exception as api_error:
                debug_print(f"⚠️ 使用API方法失败，回退到自定义方法: {str(api_error)}")
            
            # 回退到自定义的信息提取方法
            response = self.session.get(video_url, timeout=15)
            response.raise_for_status()
            
            # 解析页面内容
            enhanced_info = self._extract_enhanced_info_from_page(response.text, video_url)
            
            # 合并基础信息和增强信息
            result = basic_video_info.copy()
            result.update(enhanced_info)
            
            # 确保封面图片URL正确
            if not result.get("thumbnail") or result.get("thumbnail").startswith('data:'):
                result["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-n.jpg"
            
            return result
            
        except Exception as e:
            debug_print(f"⚠️ 获取增强信息出错: {str(e)}")
            # 即使获取增强信息失败，也要确保封面图片URL正确
            result = basic_video_info.copy()
            if video_code and (not result.get("thumbnail") or result.get("thumbnail").startswith('data:')):
                result["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-n.jpg"
            return result
    
    def _extract_enhanced_info_from_page(self, html_content: str, url: str) -> Dict:
        """从视频页面提取增强信息"""
        enhanced_info = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text()
            
            # 提取精确的时长信息
            duration_patterns = [
                r'时长[：:]\s*(\d{1,2}:\d{2}:\d{2})',
                r'時長[：:]\s*(\d{1,2}:\d{2}:\d{2})',
                r'duration[：:]\s*(\d{1,2}:\d{2}:\d{2})',
                r'(\d{1,2}:\d{2}:\d{2})'
            ]
            
            for pattern in duration_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    enhanced_info["duration"] = match.group(1)
                    enhanced_info["precise_duration"] = match.group(1)
                    break
            
            # 提取演员信息（带链接）- 多种方式
            actresses_info = []
            
            # 方式1: 通过链接查找
            actress_links = soup.find_all('a', href=re.compile(r'/actress/|/actresses/'))
            for link in actress_links:
                actress_name = link.get_text(strip=True)
                actress_url = link.get('href')
                if actress_name and len(actress_name) > 1 and not actress_name.lower() in ['actress', 'actresses']:
                    actresses_info.append({
                        "name": actress_name,
                        "url": urljoin(self.base_url, actress_url) if actress_url.startswith('/') else actress_url
                    })
            
            # 方式2: 通过文本模式查找
            if not actresses_info:
                actress_patterns = [
                    r'演员[：:]\s*([^，,\n\r]+)',
                    r'女优[：:]\s*([^，,\n\r]+)',
                    r'主演[：:]\s*([^，,\n\r]+)',
                    r'出演[：:]\s*([^，,\n\r]+)'
                ]
                
                for pattern in actress_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        names = [name.strip() for name in re.split(r'[，,、]', match) if name.strip()]
                        for name in names:
                            if len(name) > 1:
                                actresses_info.append({"name": name, "url": ""})
            
            if actresses_info:
                enhanced_info["actresses_with_links"] = actresses_info
                enhanced_info["actresses"] = [actress["name"] for actress in actresses_info]
            
            # 提取类型/标签信息（带链接）- 多种方式
            tags_info = []
            
            # 方式1: 通过链接查找
            tag_links = soup.find_all('a', href=re.compile(r'/tag/|/genre/|/genres/'))
            for link in tag_links:
                tag_name = link.get_text(strip=True)
                tag_url = link.get('href')
                if tag_name and len(tag_name) > 1 and not tag_name.lower() in ['tag', 'tags', 'genre', 'genres']:
                    tags_info.append({
                        "name": tag_name,
                        "url": urljoin(self.base_url, tag_url) if tag_url.startswith('/') else tag_url
                    })
            
            # 方式2: 通过文本模式查找
            if not tags_info:
                tag_patterns = [
                    r'类型[：:]\s*([^，,\n\r]+)',
                    r'标签[：:]\s*([^，,\n\r]+)',
                    r'分类[：:]\s*([^，,\n\r]+)',
                    r'類型[：:]\s*([^，,\n\r]+)',
                    r'標籤[：:]\s*([^，,\n\r]+)'
                ]
                
                for pattern in tag_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        tags = [tag.strip() for tag in re.split(r'[，,、]', match) if tag.strip()]
                        for tag in tags:
                            if len(tag) > 1:
                                tags_info.append({"name": tag, "url": ""})
            
            if tags_info:
                enhanced_info["tags_with_links"] = tags_info
                enhanced_info["tags"] = [tag["name"] for tag in tags_info]
            
            # 提取系列信息 - 多种方式
            series_links = soup.find_all('a', href=re.compile(r'/series/'))
            if series_links:
                series_link = series_links[0]
                enhanced_info["series"] = series_link.get_text(strip=True)
                enhanced_info["series_url"] = urljoin(self.base_url, series_link.get('href'))
            else:
                # 通过文本模式查找
                series_patterns = [
                    r'系列[：:]\s*([^，,\n\r]+)',
                    r'シリーズ[：:]\s*([^，,\n\r]+)'
                ]
                for pattern in series_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        enhanced_info["series"] = match.group(1).strip()
                        break
            
            # 提取发行商信息 - 多种方式
            studio_links = soup.find_all('a', href=re.compile(r'/studio/|/studios/'))
            if studio_links:
                studio_link = studio_links[0]
                enhanced_info["studio"] = studio_link.get_text(strip=True)
                enhanced_info["studio_url"] = urljoin(self.base_url, studio_link.get('href'))
            else:
                # 通过文本模式查找
                studio_patterns = [
                    r'发行商[：:]\s*([^，,\n\r]+)',
                    r'制作商[：:]\s*([^，,\n\r]+)',
                    r'發行商[：:]\s*([^，,\n\r]+)',
                    r'製作商[：:]\s*([^，,\n\r]+)',
                    r'スタジオ[：:]\s*([^，,\n\r]+)',
                    r'メーカー[：:]\s*([^，,\n\r]+)'
                ]
                for pattern in studio_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        enhanced_info["studio"] = match.group(1).strip()
                        break
            
            # 提取发行日期
            date_patterns = [
                r'发行日期[：:]\s*(\d{4}-\d{2}-\d{2})',
                r'發行日期[：:]\s*(\d{4}-\d{2}-\d{2})',
                r'release[：:]\s*(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    enhanced_info["release_date"] = match.group(1)
                    break
            
            # 提取视频简介/描述 - 多种方式
            description_selectors = [
                'div.description',
                'div.summary',
                'div.plot',
                'p.description',
                'div.content',
                'div.intro',
                '.video-description',
                '.video-summary'
            ]
            
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description and len(description) > 10:
                        enhanced_info["description"] = description
                        break
            
            # 如果没有找到描述，尝试从meta标签获取
            if not enhanced_info.get("description"):
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    description = meta_desc.get('content').strip()
                    if len(description) > 10:
                        enhanced_info["description"] = description
            
            # 提取标签信息（更详细的方式）
            labels_info = []
            label_links = soup.find_all('a', href=re.compile(r'/labels/'))
            for link in label_links:
                label_name = link.get_text(strip=True)
                label_url = link.get('href')
                if label_name and len(label_name) > 1:
                    labels_info.append({
                        "name": label_name,
                        "url": urljoin(self.base_url, label_url) if label_url.startswith('/') else label_url
                    })
            
            if labels_info:
                enhanced_info["labels_with_links"] = labels_info
                enhanced_info["labels"] = [label["name"] for label in labels_info]
            
            # 提取制作商信息（makers）
            maker_links = soup.find_all('a', href=re.compile(r'/makers/'))
            if maker_links:
                maker_link = maker_links[0]
                enhanced_info["maker"] = maker_link.get_text(strip=True)
                enhanced_info["maker_url"] = urljoin(self.base_url, maker_link.get('href'))
            
            # 提取可用分辨率信息（增强版）
            resolution_info = self._extract_detailed_resolution_from_page(html_content, soup)
            if resolution_info:
                enhanced_info.update(resolution_info)
            
            # 提取预览视频信息
            preview_info = self._extract_preview_info_from_page(html_content, soup, url)
            if preview_info:
                enhanced_info.update(preview_info)
            
            # 提取M3U8播放链接
            m3u8_info = self._extract_m3u8_info_from_page(html_content, soup)
            if m3u8_info:
                enhanced_info.update(m3u8_info)
            
            # 提取观看次数和评分信息
            views_patterns = [
                r'观看[：:]\s*(\d+)',
                r'播放[：:]\s*(\d+)',
                r'(\d+)\s*次观看',
                r'(\d+)\s*views',
                r'觀看[：:]\s*(\d+)'
            ]
            
            for pattern in views_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    enhanced_info["views"] = match.group(1)
                    enhanced_info["view_count"] = match.group(1)
                    break
            
            # 提取评分信息
            rating_patterns = [
                r'评分[：:]\s*(\d+\.?\d*)',
                r'評分[：:]\s*(\d+\.?\d*)',
                r'★\s*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*分',
                r'rating[：:]\s*(\d+\.?\d*)'
            ]
            
            for pattern in rating_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    enhanced_info["rating"] = match.group(1)
                    break
            
            # 提取封面图片信息（高清版本）
            cover_imgs = soup.find_all('img', src=re.compile(r'cover|thumb'))
            if cover_imgs:
                main_cover = cover_imgs[0].get('src')
                if main_cover and not main_cover.startswith('data:'):
                    enhanced_info["main_cover"] = urljoin(self.base_url, main_cover) if main_cover.startswith('/') else main_cover
            
            # 尝试获取高清封面
            video_code = self._extract_video_code_from_url(url)
            if video_code:
                enhanced_info["cover_image"] = f"https://fourhoi.com/{video_code}/cover-n.jpg"
            
        except Exception as e:
            debug_print(f"⚠️ 解析增强信息时出错: {str(e)}")
        
        return enhanced_info
    
    def _extract_detailed_resolution_from_page(self, html_content: str, soup) -> Dict:
        """从页面提取详细的分辨率信息"""
        resolution_info = {}
        
        try:
            # 查找JavaScript中的分辨率信息
            resolution_patterns = [
                r'"(\d{3,4}p)"\s*:\s*"([^"]+)"',  # "1080p": "1920x1080"
                r'(\d{3,4}p)\s*\((\d+x\d+)\)',    # 1080p (1920x1080)
                r'(\d{3,4})x(\d{3,4})',           # 1920x1080
                r'"quality":\s*"(\d{3,4}p)"',     # "quality": "1080p"
            ]
            
            available_resolutions = []
            
            for pattern in resolution_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        if 'p' in match[0]:
                            quality = match[0]
                            resolution = match[1] if 'x' in match[1] else f"{match[1]}x{match[0].replace('p', '')}"
                        else:
                            quality = f"{match[1]}p"
                            resolution = f"{match[0]}x{match[1]}"
                        
                        available_resolutions.append({
                            "quality": quality,
                            "resolution": resolution
                        })
            
            # 标准分辨率映射
            standard_resolutions = {
                "360p": "640x360",
                "480p": "854x480", 
                "720p": "1280x720",
                "1080p": "1920x1080",
                "1440p": "2560x1440",
                "2160p": "3840x2160"  # 4K
            }
            
            # 如果没有找到具体分辨率，使用标准映射和默认分辨率
            if not available_resolutions:
                # 查找更多分辨率模式
                quality_matches = re.findall(r'(\d{3,4}p)', html_content, re.IGNORECASE)
                found_qualities = set()
                
                for quality in quality_matches:
                    quality_lower = quality.lower()
                    if quality_lower in standard_resolutions and quality_lower not in found_qualities:
                        available_resolutions.append({
                            "quality": quality,
                            "resolution": standard_resolutions[quality_lower]
                        })
                        found_qualities.add(quality_lower)
                
                # 如果还是没有找到，使用默认的常见分辨率
                if not available_resolutions:
                    default_resolutions = [
                        {"quality": "360p", "resolution": "640x360"},
                        {"quality": "480p", "resolution": "854x480"},
                        {"quality": "720p", "resolution": "1280x720"},
                        {"quality": "1080p", "resolution": "1920x1080"}
                    ]
                    available_resolutions = default_resolutions
            
            if available_resolutions:
                # 去重并排序
                unique_resolutions = []
                seen = set()
                for res in available_resolutions:
                    key = res["quality"].lower()
                    if key not in seen:
                        unique_resolutions.append(res)
                        seen.add(key)
                
                # 按质量排序
                quality_order = {"2160p": 0, "1440p": 1, "1080p": 2, "720p": 3, "480p": 4, "360p": 5}
                unique_resolutions.sort(key=lambda x: quality_order.get(x["quality"].lower(), 99))
                
                resolution_info["available_resolutions"] = unique_resolutions
                resolution_info["resolution_count"] = len(unique_resolutions)
                
                if unique_resolutions:
                    resolution_info["best_quality"] = unique_resolutions[0]["quality"]
                    resolution_info["best_resolution"] = unique_resolutions[0]["resolution"]
            
        except Exception as e:
            debug_print(f"⚠️ 提取详细分辨率信息时出错: {str(e)}")
        
        return resolution_info
    
    def _extract_preview_info_from_page(self, html_content: str, soup, url: str) -> Dict:
        """从页面提取预览视频信息"""
        preview_info = {}
        
        try:
            video_code = self._extract_video_code_from_url(url)
            
            # 查找预览视频链接
            preview_patterns = [
                r'"preview":\s*"([^"]+)"',
                r'preview["\']?\s*:\s*["\']([^"\']+)["\']',
                r'preview\.mp4["\']?\s*:\s*["\']([^"\']+)["\']',
                r'(https?://[^"\s]+/preview\.mp4)',
                r'(https?://fourhoi\.com/[^/]+/preview\.mp4)'
            ]
            
            preview_urls = []
            for pattern in preview_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                preview_urls.extend(matches)
            
            # 构建标准预览URL
            if video_code:
                standard_preview = f"https://fourhoi.com/{video_code}/preview.mp4"
                preview_urls.append(standard_preview)
            
            if preview_urls:
                # 去重
                unique_previews = list(set(preview_urls))
                preview_info["preview_videos"] = unique_previews
                preview_info["preview_count"] = len(unique_previews)
                preview_info["main_preview"] = unique_previews[0]
            
        except Exception as e:
            debug_print(f"⚠️ 提取预览视频信息时出错: {str(e)}")
        
        return preview_info
    
    def _extract_m3u8_info_from_page(self, html_content: str, soup) -> Dict:
        """从页面提取M3U8播放链接信息"""
        m3u8_info = {}
        
        try:
            # 首先尝试直接查找M3U8链接
            m3u8_patterns = [
                r'"(https?://[^"]+\.m3u8[^"]*)"',
                r"'(https?://[^']+\.m3u8[^']*)'",
                r'src:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'playlist["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'(https?://surrit\.com/[^/]+/playlist\.m3u8)',
                r'(https?://[^"\s]+/playlist\.m3u8)'
            ]
            
            m3u8_urls = []
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                m3u8_urls.extend(matches)
            
            # 如果直接搜索没有结果，尝试解码混淆的JavaScript
            if not m3u8_urls:
                m3u8_urls = self._decode_obfuscated_js_for_m3u8(html_content)
            
            if m3u8_urls:
                # 去重
                unique_m3u8 = list(set(m3u8_urls))
                m3u8_info["m3u8_playlists"] = unique_m3u8
                m3u8_info["m3u8_count"] = len(unique_m3u8)
                m3u8_info["main_m3u8"] = unique_m3u8[0]
            
        except Exception as e:
            debug_print(f"⚠️ 提取M3U8信息时出错: {str(e)}")
        
        return m3u8_info
    
    def _decode_obfuscated_js_for_m3u8(self, html_content: str) -> List[str]:
        """解码混淆的JavaScript来查找M3U8链接"""
        m3u8_urls = []
        
        try:
            # 查找混淆的JavaScript代码
            obfuscated_patterns = [
                r'eval\(function\(p,a,c,k,e,d\)\{[^}]+\}[^)]+\)',
                r'eval\([^)]+\)'
            ]
            
            for pattern in obfuscated_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        # 尝试简单的字符串替换解码
                        decoded = self._simple_js_decode(match)
                        if decoded:
                            # 在解码后的内容中查找M3U8链接
                            m3u8_patterns = [
                                r'(https?://[^"\s\']+\.m3u8[^"\s\']*)',
                                r'(https?://surrit\.com/[^/\s"\']+/playlist\.m3u8)',
                            ]
                            
                            for m3u8_pattern in m3u8_patterns:
                                found_urls = re.findall(m3u8_pattern, decoded, re.IGNORECASE)
                                m3u8_urls.extend(found_urls)
                    except:
                        continue
            
            # 如果还是没有找到，尝试查找base64编码的内容
            if not m3u8_urls:
                m3u8_urls = self._find_base64_m3u8(html_content)
            
        except Exception as e:
            debug_print(f"⚠️ 解码混淆JavaScript时出错: {str(e)}")
        
        return m3u8_urls
    
    def _simple_js_decode(self, obfuscated_code: str) -> str:
        """简单的JavaScript解码"""
        try:
            # 查找字符串数组
            array_match = re.search(r'\[([^\]]+)\]', obfuscated_code)
            if not array_match:
                return ""
            
            # 提取字符串数组
            array_content = array_match.group(1)
            strings = []
            
            # 解析字符串数组
            string_matches = re.findall(r'["\']([^"\']*)["\']', array_content)
            strings.extend(string_matches)
            
            # 尝试重建原始字符串
            decoded_parts = []
            for s in strings:
                if 'surrit' in s or 'm3u8' in s or 'playlist' in s:
                    decoded_parts.append(s)
            
            return ' '.join(decoded_parts)
            
        except Exception as e:
            debug_print(f"⚠️ 简单JS解码失败: {str(e)}")
            return ""
    
    def _find_base64_m3u8(self, html_content: str) -> List[str]:
        """查找可能的base64编码的M3U8链接"""
        m3u8_urls = []
        
        try:
            import base64
            
            # 查找可能的base64编码字符串
            base64_patterns = [
                r'[A-Za-z0-9+/]{20,}={0,2}',  # 基本base64模式
            ]
            
            for pattern in base64_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                        if 'm3u8' in decoded.lower() or 'surrit' in decoded.lower():
                            # 在解码内容中查找URL
                            url_matches = re.findall(r'https?://[^\s"\'<>]+', decoded)
                            for url in url_matches:
                                if 'm3u8' in url.lower():
                                    m3u8_urls.append(url)
                    except:
                        continue
            
        except Exception as e:
            debug_print(f"⚠️ Base64解码失败: {str(e)}")
        
        return m3u8_urls
    
    def _extract_video_info_from_link_enhanced(self, link) -> Optional[Dict]:
        """从链接元素中提取信息 - 增强版"""
        try:
            href = link.get('href', '')
            if href.startswith('/'):
                href = urljoin(self.base_url, href)
            elif not href.startswith('http'):
                href = urljoin(self.base_url, '/' + href)
            
            video_info = {
                "url": href,
                "video_code": self._extract_video_code_from_url(href),
                "title": "",
                "thumbnail": "",
                "duration": "",
                "publish_date": "",
                "views": ""
            }
            
            # 提取标题 - 增强版
            title = link.get_text(strip=True) or link.get('title', '') or link.get('alt', '')
            
            if not title:
                # 尝试从子元素获取
                title_elem = link.find(['span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            if not title:
                # 尝试从父元素获取标题
                parent = link.parent
                if parent:
                    # 查找标题相关的元素
                    title_selectors = [
                        '.title', '.video-title', '.name', '.video-name',
                        '[class*="title"]', '[class*="name"]'
                    ]
                    for selector in title_selectors:
                        title_elem = parent.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            break
                    
                    # 如果还是没有，尝试从兄弟元素获取
                    if not title:
                        for sibling in parent.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            sibling_text = sibling.get_text(strip=True)
                            if sibling_text and len(sibling_text) > 10:  # 标题通常比较长
                                title = sibling_text
                                break
            
            video_info["title"] = title
            
            # 尝试从父元素或兄弟元素中提取更多信息
            parent = link.parent
            if parent:
                # 查找缩略图
                img = parent.find('img')
                if img:
                    src = (img.get('src') or img.get('data-src') or 
                          img.get('data-lazy') or img.get('data-original'))
                    if src:
                        if src.startswith('/'):
                            src = urljoin(self.base_url, src)
                        video_info["thumbnail"] = src
                
                # 查找时长和日期
                parent_text = parent.get_text()
                duration_match = re.search(r'\b(\d{1,2}:\d{2}(?::\d{2})?)\b', parent_text)
                if duration_match:
                    video_info["duration"] = duration_match.group(1)
                
                date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', parent_text)
                if date_match:
                    video_info["publish_date"] = date_match.group(1)
            
            return video_info
            
        except Exception as e:
            debug_print(f"❌ 提取链接信息出错: {str(e)}")
            return None
    
    def _extract_videos_with_regex(self, html_content: str) -> List[Dict]:
        """使用正则表达式直接提取视频信息"""
        results = []
        
        try:
            # 匹配MissAV视频链接的正则表达式
            video_link_patterns = [
                r'href="([^"]*(?:missav\.ws|missav\.com)[^"]*\/[a-zA-Z0-9\-]+)"',
                r'href="(\/[a-zA-Z0-9\-]+)"(?=.*video|.*thumbnail)',
                r'<a[^>]*href="([^"]*\/[a-zA-Z]{2,6}-\d{2,4}[^"]*)"'
            ]
            
            for pattern in video_link_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    url = match
                    if url.startswith('/'):
                        url = urljoin(self.base_url, url)
                    
                    if self._is_missav_video_link(url):
                        video_code = self._extract_video_code_from_url(url)
                        if video_code and len(video_code) > 2:
                            # 尝试提取标题
                            title_pattern = rf'<a[^>]*href="{re.escape(match)}"[^>]*>([^<]+)</a>'
                            title_match = re.search(title_pattern, html_content, re.IGNORECASE)
                            title = title_match.group(1).strip() if title_match else video_code
                            
                            results.append({
                                "url": url,
                                "video_code": video_code,
                                "title": title,
                                "thumbnail": "",
                                "duration": "",
                                "publish_date": "",
                                "views": ""
                            })
                
                if results:
                    break  # 如果找到结果就停止尝试其他模式
            
        except Exception as e:
            debug_print(f"❌ 正则表达式提取出错: {str(e)}")
        
        return results
    
    def _extract_videos_from_javascript(self, html_content: str) -> List[Dict]:
        """从JavaScript代码中提取视频信息"""
        results = []
        
        try:
            # 查找JavaScript中的视频数据
            js_patterns = [
                r'videos\s*:\s*(\[.*?\])',
                r'videoList\s*:\s*(\[.*?\])',
                r'data\s*:\s*(\[.*?\])',
                r'items\s*:\s*(\[.*?\])'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        import json
                        video_data = json.loads(match)
                        if isinstance(video_data, list):
                            for item in video_data:
                                if isinstance(item, dict) and 'url' in item:
                                    results.append({
                                        "url": item.get('url', ''),
                                        "video_code": item.get('code', ''),
                                        "title": item.get('title', ''),
                                        "thumbnail": item.get('thumbnail', ''),
                                        "duration": item.get('duration', ''),
                                        "publish_date": item.get('date', ''),
                                        "views": item.get('views', '')
                                    })
                    except:
                        continue
                
                if results:
                    break
            
        except Exception as e:
            debug_print(f"❌ JavaScript提取出错: {str(e)}")
        
        return results
    
    def _extract_video_info_from_link(self, link) -> Optional[Dict]:
        """从链接元素中提取信息"""
        try:
            href = link.get('href', '')
            if href.startswith('/'):
                href = urljoin(self.base_url, href)
            
            video_info = {
                "url": href,
                "video_code": self._extract_video_code_from_url(href),
                "title": link.get_text(strip=True) or link.get('title', ''),
                "thumbnail": "",
                "duration": "",
                "publish_date": "",
                "views": ""
            }
            
            # 尝试从父元素中提取更多信息
            parent = link.parent
            if parent:
                img = parent.find('img')
                if img:
                    src = img.get('src') or img.get('data-src')
                    if src and src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    video_info["thumbnail"] = src or ""
            
            return video_info
            
        except Exception as e:
            debug_print(f"提取链接信息出错: {str(e)}")
            return None
    
    def _parse_generic_video_list(self, soup) -> List[Dict]:
        """通用的视频列表解析方法"""
        results = []
        seen_codes = set()  # 用于去重
        
        try:
            # 寻找所有可能的视频链接
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                if self._is_missav_video_link(href):
                    video_info = self._extract_video_info_from_link_enhanced(link)
                    if video_info and self._is_valid_video_info(video_info):
                        # 去重：基于视频代码
                        video_code = video_info.get('video_code', '')
                        if video_code and video_code not in seen_codes:
                            results.append(video_info)
                            seen_codes.add(video_code)
                            debug_print(f"✅ 提取到唯一视频: {video_info.get('title', '无标题')} ({video_code})")
                        elif video_code in seen_codes:
                            debug_print(f"⚠️ 跳过重复视频: {video_code}")
            
        except Exception as e:
            debug_print(f"通用解析出错: {str(e)}")
        
        return results
    
    def _is_missav_video_link(self, href: str) -> bool:
        """判断是否是MissAV视频链接 - 增强版"""
        if not href:
            return False
        
        # 排除明显不是视频的链接
        exclude_patterns = [
            '/search/', '/category/', '/tag/', '/actress/', '/actresses/',
            '/studio/', '/studios/', '/series/', '/page/', '/login',
            '/register', '/contact', '/about', '/api/', '/admin/',
            '/fonts/', '/css/', '/js/', '/images/', '/img/',
            '.css', '.js', '.png', '.jpg', '.gif', '.ico', 
            '.woff', '.woff2', '.ttf', '.svg',
            '/genres/', '/uncensored-leak/', '/chinese-subtitle/',
            '/monthly-hot/', '/weekly-hot/', '/daily-hot/',
            '/new/', '/popular/', '/trending/', '/dm22/', '/dm54/',
            '/dm4416/', '/dm621/', '/dm291/', '/dm169/', '/dm257/',
            '?sort=', '?filters=', '?page=', '#'
        ]
        
        for pattern in exclude_patterns:
            if pattern in href:
                return False
        
        # 额外检查：排除以这些无效代码结尾的链接
        invalid_endings = [
            '/uncensored-leak', '/chinese-subtitle', '/english-subtitle',
            '/today-hot', '/weekly-hot', '/monthly-hot', '/new', '/popular',
            '/trending', '/search', '/genres', '/category'
        ]
        
        href_clean = href.split('?')[0].split('#')[0]  # 移除查询参数和锚点
        for ending in invalid_endings:
            if href_clean.endswith(ending):
                return False
        
        # MissAV视频链接的特征模式
        video_patterns = [
            # 标准格式：字母-数字 (如 /SSIS-950, /OFJE-505)
            r'/[A-Z]{2,6}-\d{2,4}$',
            # 带后缀的格式 (如 /SSIS-950-uncensored)
            r'/[A-Z]{2,6}-\d{2,4}-[a-z-]+$',
            # 数字开头的格式 (如 /259LUXU-1234)
            r'/\d{2,4}[A-Z]{2,6}-\d{2,4}$',
            # 特殊格式 (如 /FC2-PPV-1234567)
            r'/FC2-PPV-\d{6,8}$',
            # 其他常见格式
            r'/[A-Z]{1,4}\d{2,4}$',  # 如 /ABP123
            # 小写格式
            r'/[a-z]{2,6}-\d{2,4}$',
            # 混合格式
            r'/[A-Za-z0-9]{3,10}-[A-Za-z0-9]{2,6}$'
        ]
        
        # 提取URL路径部分进行匹配
        url_path = href.split('?')[0].split('#')[0]  # 移除查询参数和锚点
        
        # 检查是否匹配视频代码模式
        for pattern in video_patterns:
            if re.search(pattern, url_path, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_video_code_from_url(self, url: str) -> str:
        """从URL中提取视频代码"""
        try:
            path = urlparse(url).path
            code = path.split('/')[-1]
            return code if code else ""
        except:
            return ""
    
    def _is_valid_video_info(self, video_info: Dict) -> bool:
        """验证视频信息是否有效 - 增强版"""
        if not video_info:
            return False
        
        url = video_info.get("url", "")
        video_code = video_info.get("video_code", "")
        title = video_info.get("title", "")
        
        # 基本验证
        if not url or not video_code:
            return False
        
        # 视频代码长度验证
        if len(video_code) < 2:
            return False
        
        # URL有效性验证
        if not self._is_missav_video_link(url):
            return False
        
        # 排除明显的错误结果
        invalid_codes = [
            'search', 'page', 'sort', 'filter', 'genres', 'category',
            'english-subtitle', 'chinese-subtitle', 'uncensored-leak',
            'today-hot', 'weekly-hot', 'monthly-hot', 'dm22', 'dm54', 'dm4416'
        ]
        
        if video_code.lower() in invalid_codes:
            return False
        
        # 检查是否是URL编码的关键词（如%E6%8A%A4%E5%A3%AB）
        if '%' in video_code and len(video_code) > 10:
            return False
        
        return True


def test_unified_search():
    """测试统一搜索模块"""
    debug_print("🧪 测试统一搜索模块")
    debug_print("=" * 50)
    
    search_module = UnifiedSearchModule()
    
    # 测试1: 基础搜索
    debug_print("\n--- 测试1: 基础搜索 ---")
    result = search_module.search_with_filters("SSIS", page=1, max_results=5)
    if result["success"]:
        debug_print(f"✅ 基础搜索成功，找到 {result['total_count']} 个结果")
        for i, video in enumerate(result["results"][:3]):
            debug_print(f"  {i+1}. {video['title']} ({video['video_code']})")
    else:
        debug_print(f"❌ 基础搜索失败: {result['error']}")
    
    # 测试2: 带排序的搜索
    debug_print("\n--- 测试2: 带排序的搜索 ---")
    result = search_module.search_with_filters("OFJE", page=1, sort="views", max_results=5)
    if result["success"]:
        debug_print(f"✅ 排序搜索成功，找到 {result['total_count']} 个结果")
        debug_print(f"   排序方式: {result['sort_name']}")
        for i, video in enumerate(result["results"][:3]):
            debug_print(f"  {i+1}. {video['title']} ({video['video_code']})")
    else:
        debug_print(f"❌ 排序搜索失败: {result['error']}")
    
    # 测试3: 带过滤器的搜索
    debug_print("\n--- 测试3: 带过滤器的搜索 ---")
    result = search_module.search_with_filters("STARS", page=1, filter_type="chinese_subtitle", max_results=5)
    if result["success"]:
        debug_print(f"✅ 过滤器搜索成功，找到 {result['total_count']} 个结果")
        debug_print(f"   过滤器: {result['filter_name']}")
        for i, video in enumerate(result["results"][:3]):
            debug_print(f"  {i+1}. {video['title']} ({video['video_code']})")
    else:
        debug_print(f"❌ 过滤器搜索失败: {result['error']}")
    
    # 测试4: 排序+过滤器组合
    debug_print("\n--- 测试4: 排序+过滤器组合 ---")
    result = search_module.search_with_filters(
        "High School Girl", page=1, sort="today_views", 
        filter_type="individual", max_results=5
    )
    if result["success"]:
        debug_print(f"✅ 组合搜索成功，找到 {result['total_count']} 个结果")
        debug_print(f"   排序方式: {result['sort_name']}")
        debug_print(f"   过滤器: {result['filter_name']}")
        for i, video in enumerate(result["results"][:3]):
            debug_print(f"  {i+1}. {video['title']} ({video['video_code']})")
    else:
        debug_print(f"❌ 组合搜索失败: {result['error']}")
    
    # 测试5: 热榜功能
    debug_print("\n--- 测试5: 热榜功能 ---")
    result = search_module.get_hot_videos_with_filters("daily", page=1, sort="views")
    if result["success"]:
        debug_print(f"✅ 热榜获取成功，找到 {result['total_count']} 个结果")
        debug_print(f"   数据源: {result['source']}")
        for i, video in enumerate(result["results"][:3]):
            debug_print(f"  {i+1}. {video['title']} ({video['video_code']})")
    else:
        debug_print(f"❌ 热榜获取失败: {result['error']}")
    
    debug_print("\n✅ 统一搜索模块测试完成")


if __name__ == "__main__":
    test_unified_search()