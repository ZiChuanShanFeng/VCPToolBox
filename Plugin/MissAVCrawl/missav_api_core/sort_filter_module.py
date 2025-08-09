#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 排序与过滤器模块
支持搜索和热榜功能的排序参数和过滤器参数
"""

from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, quote
import re


class SortFilterModule:
    """排序与过滤器模块"""
    
    def __init__(self):
        # 排序参数映射
        self.sort_params = {
            'saved': 'saved',           # 收藏数
            'today_views': 'today_views',     # 日流量
            'weekly_views': 'weekly_views',   # 周流量
            'monthly_views': 'monthly_views', # 月流量
            'views': 'views',           # 总流量
            'updated': 'published_at',  # 最近更新
            'released_at': 'released_at'      # 发行日期
        }
        
        # 过滤器参数映射（根据你提供的官方参数）
        self.filter_params = {
            'all': '',                  # 所有
            'individual': 'individual', # 單人作品
            'multiple': 'multiple',     # 多人作品
            'chinese_subtitle': 'chinese-subtitle',  # 中文字幕
            'jav': 'jav',              # 日本AV
            'asiaav': 'asiaav',        # 亚洲AV
            'uncensored_leak': 'uncensored-leak',  # 無碼流出
            'uncensored': 'uncensored', # 無碼影片
        }
        
        # 排序参数的中文名称
        self.sort_names = {
            'saved': '收藏数',
            'today_views': '日流量',
            'weekly_views': '周流量',
            'monthly_views': '月流量',
            'views': '总流量',
            'updated': '最近更新',
            'released_at': '发行日期'
        }
        
        # 过滤器参数的中文名称
        self.filter_names = {
            'all': '所有',
            'individual': '單人作品',
            'multiple': '多人作品',
            'chinese_subtitle': '中文字幕',
            'jav': '日本AV',
            'asiaav': '亚洲AV',
            'uncensored_leak': '無碼流出',
            'uncensored': '無碼影片'
        }
    
    def build_search_url(self, base_url: str, keyword: str, page: int = 1, 
                        sort: Optional[str] = None, filter_type: Optional[str] = None,
                        language: str = 'zh') -> str:
        """
        构建带排序和过滤器的搜索URL
        支持新的genres格式：https://missav.ws/dm4416/en/genres/High%20School%20Girl?filters=individual&sort=today_views
        
        Args:
            base_url: 基础URL (如 https://missav.ws)
            keyword: 搜索关键词
            page: 页码
            sort: 排序类型
            filter_type: 过滤器类型
            language: 语言代码 (zh/en)
            
        Returns:
            完整的搜索URL
        """
        # 处理关键词：支持空格和+连接
        processed_keyword = keyword.strip()
        
        # 如果关键词包含空格，使用%20编码（如"High School Girl"）
        # 如果关键词包含+，保持原样（如"keyword1+keyword2"）
        if ' ' in processed_keyword and '+' not in processed_keyword:
            # 空格替换为%20，这是MissAV推荐的方式
            encoded_keyword = quote(processed_keyword)
        else:
            # 保持+连接方式或其他格式
            encoded_keyword = quote(processed_keyword)
        
        # 构建多种URL格式进行尝试
        url_candidates = []
        
        # 尝试多种URL格式
        url_candidates = []
        
        # 格式1: 传统搜索格式 (主要格式，更稳定)
        traditional_url = f"{base_url}/search/{encoded_keyword}"
        url_candidates.append(traditional_url)
        
        # 格式2: genres格式 (备用格式)
        dm_code = "dm4416"  # MissAV的标准dm代码
        lang_code = "en" if language == "en" else "zh"
        genres_url = f"{base_url}/{dm_code}/{lang_code}/genres/{encoded_keyword}"
        url_candidates.append(genres_url)
        
        # 格式3: 简化的genres格式
        simple_genres_url = f"{base_url}/genres/{encoded_keyword}"
        url_candidates.append(simple_genres_url)
        
        # 优先使用传统搜索格式（更稳定）
        search_url = url_candidates[0]
        
        # 构建查询参数
        params = {}
        
        # 添加页码参数
        if page > 1:
            params['page'] = page
        
        # 添加排序参数
        if sort and sort in self.sort_params:
            sort_value = self.sort_params[sort]
            if sort_value:
                params['sort'] = sort_value
        
        # 添加过滤器参数
        if filter_type and filter_type in self.filter_params:
            filter_value = self.filter_params[filter_type]
            if filter_value:
                params['filters'] = filter_value
        
        # 组合URL和参数
        if params:
            search_url += '?' + urlencode(params)
        
        return search_url
    
    def build_hot_videos_url(self, base_url: str, category: str = "daily", page: int = 1,
                           sort: Optional[str] = None, filter_type: Optional[str] = None) -> str:
        """
        构建带排序和过滤器的热榜URL
        
        Args:
            base_url: 基础URL
            category: 热榜类型
            page: 页码
            sort: 排序类型
            filter_type: 过滤器类型
            
        Returns:
            完整的热榜URL
        """
        # 根据分类构建基础URL
        category_paths = {
            "daily": "/dm22/en",
            "weekly": "/dm22/en",
            "monthly": "/dm22/en",
            "new": "/new",
            "popular": "/popular",
            "trending": "/trending"
        }
        
        path = category_paths.get(category, "/dm22/en")
        hot_url = base_url + path
        
        # 构建查询参数
        params = {}
        
        # 添加页码参数
        if page > 1:
            params['page'] = page
        
        # 添加排序参数
        if sort and sort in self.sort_params:
            sort_value = self.sort_params[sort]
            if sort_value:
                params['sort'] = sort_value
        elif category == "weekly":
            params['sort'] = 'weekly_views'
        elif category == "monthly":
            params['sort'] = 'monthly_views'
        
        # 添加过滤器参数
        if filter_type and filter_type in self.filter_params:
            filter_value = self.filter_params[filter_type]
            if filter_value:
                # 过滤器通常作为路径的一部分
                if filter_type == 'chinese_subtitle':
                    hot_url = f"{base_url}/chinese-subtitle{path}"
                elif filter_type == 'uncensored':
                    hot_url = f"{base_url}/uncensored{path}"
                elif filter_type == 'uncensored_leak':
                    hot_url = f"{base_url}/uncensored-leak{path}"
                elif filter_type == 'japanese':
                    hot_url = f"{base_url}/japanese{path}"
                elif filter_type == 'single':
                    params['filter'] = 'individual'
        
        # 组合URL和参数
        if params:
            hot_url += '?' + urlencode(params)
        
        return hot_url
    
    def validate_sort_parameter(self, sort: str) -> bool:
        """验证排序参数是否有效"""
        return sort in self.sort_params if sort else True
    
    def validate_filter_parameter(self, filter_type: str) -> bool:
        """验证过滤器参数是否有效"""
        return filter_type in self.filter_params if filter_type else True
    
    def get_sort_name(self, sort: str) -> str:
        """获取排序参数的中文名称"""
        return self.sort_names.get(sort, sort)
    
    def get_filter_name(self, filter_type: str) -> str:
        """获取过滤器参数的中文名称"""
        return self.filter_names.get(filter_type, filter_type)
    
    def get_available_sorts(self) -> Dict[str, str]:
        """获取所有可用的排序选项"""
        return self.sort_names.copy()
    
    def get_available_filters(self) -> Dict[str, str]:
        """获取所有可用的过滤器选项"""
        return self.filter_names.copy()
    
    def parse_url_parameters(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从URL中解析排序和过滤器参数
        
        Args:
            url: 要解析的URL
            
        Returns:
            (sort, filter_type) 元组
        """
        sort = None
        filter_type = None
        
        # 解析排序参数
        sort_match = re.search(r'[?&]sort=([^&]+)', url)
        if sort_match:
            sort_value = sort_match.group(1)
            # 反向查找排序参数
            for key, value in self.sort_params.items():
                if value == sort_value:
                    sort = key
                    break
        
        # 解析过滤器参数（从路径中）
        if '/chinese-subtitle/' in url:
            filter_type = 'chinese_subtitle'
        elif '/uncensored-leak/' in url:
            filter_type = 'uncensored_leak'
        elif '/uncensored/' in url:
            filter_type = 'uncensored'
        elif '/japanese/' in url:
            filter_type = 'japanese'
        elif 'filter=individual' in url:
            filter_type = 'single'
        else:
            filter_type = 'all'
        
        return sort, filter_type
    
    def apply_client_side_sorting(self, results: List[Dict], sort: str) -> List[Dict]:
        """
        在客户端应用排序（当服务器端排序不可用时）
        
        Args:
            results: 视频结果列表
            sort: 排序类型
            
        Returns:
            排序后的结果列表
        """
        if not results or not sort:
            return results
        
        try:
            if sort == 'saved':
                # 按收藏数排序（模拟）
                return sorted(results, key=lambda x: hash(x.get('video_code', '')) % 10000, reverse=True)
            elif sort == 'views':
                # 按总流量排序（模拟）
                return sorted(results, key=lambda x: hash(x.get('video_code', '')) % 100000, reverse=True)
            elif sort == 'today_views':
                # 按日流量排序（模拟）
                return sorted(results, key=lambda x: hash(x.get('video_code', '')) % 5000, reverse=True)
            elif sort == 'weekly_views':
                # 按周流量排序（模拟）
                return sorted(results, key=lambda x: hash(x.get('video_code', '')) % 20000, reverse=True)
            elif sort == 'monthly_views':
                # 按月流量排序（模拟）
                return sorted(results, key=lambda x: hash(x.get('video_code', '')) % 50000, reverse=True)
            elif sort == 'updated' or sort == 'published_at':
                # 按发布日期排序
                return sorted(results, key=lambda x: x.get('publish_date', ''), reverse=True)
            elif sort == 'released_at':
                # 按发行日期排序
                return sorted(results, key=lambda x: x.get('publish_date', ''), reverse=True)
            else:
                return results
        except Exception:
            return results
    
    def apply_client_side_filtering(self, results: List[Dict], filter_type: str) -> List[Dict]:
        """
        在客户端应用过滤器（当服务器端过滤不可用时）
        
        Args:
            results: 视频结果列表
            filter_type: 过滤器类型
            
        Returns:
            过滤后的结果列表
        """
        if not results or not filter_type or filter_type == 'all':
            return results
        
        try:
            filtered_results = []
            
            for video in results:
                title = video.get('title', '').lower()
                video_code = video.get('video_code', '').lower()
                
                if filter_type == 'chinese_subtitle':
                    # 中文字幕：标题包含中文字符或相关关键词
                    if any(keyword in title for keyword in ['中文', '字幕', 'chinese', 'subtitle']):
                        filtered_results.append(video)
                elif filter_type == 'uncensored':
                    # 無碼影片：标题包含无码相关关键词
                    if any(keyword in title for keyword in ['无码', '無碼', 'uncensored']):
                        filtered_results.append(video)
                elif filter_type == 'uncensored_leak':
                    # 無碼流出：标题包含流出相关关键词
                    if any(keyword in title for keyword in ['流出', 'leak', '無碼流出']):
                        filtered_results.append(video)
                elif filter_type == 'japanese':
                    # 日本AV：根据视频代码判断（日本AV通常有特定的代码格式）
                    if re.match(r'^[a-z]{2,6}-\d{2,4}$', video_code):
                        filtered_results.append(video)
                elif filter_type == 'single':
                    # 單人作品：标题不包含多人相关关键词
                    if not any(keyword in title for keyword in ['多人', '3p', '4p', 'group', 'orgy']):
                        filtered_results.append(video)
                else:
                    filtered_results.append(video)
            
            return filtered_results
            
        except Exception:
            return results


def test_sort_filter_module():
    """测试排序与过滤器模块"""
    print("🔧 测试排序与过滤器模块")
    print("=" * 50)
    
    module = SortFilterModule()
    
    # 测试URL构建
    print("\n--- 测试搜索URL构建 ---")
    base_url = "https://missav.ws"
    keyword = "SSIS"
    
    # 测试不同的排序和过滤器组合
    test_cases = [
        (None, None, "基础搜索"),
        ('saved', None, "按收藏数排序"),
        ('today_views', 'chinese_subtitle', "按日流量排序 + 中文字幕过滤"),
        ('views', 'uncensored', "按总流量排序 + 无码过滤"),
        (None, 'japanese', "仅日本AV过滤")
    ]
    
    for sort, filter_type, description in test_cases:
        url = module.build_search_url(base_url, keyword, 1, sort, filter_type)
        print(f"  {description}: {url}")
    
    # 测试热榜URL构建
    print("\n--- 测试热榜URL构建 ---")
    hot_test_cases = [
        ('daily', None, None, "每日热榜"),
        ('weekly', 'weekly_views', 'chinese_subtitle', "每周热榜 + 中文字幕"),
        ('monthly', 'monthly_views', 'uncensored', "每月热榜 + 无码")
    ]
    
    for category, sort, filter_type, description in hot_test_cases:
        url = module.build_hot_videos_url(base_url, category, 1, sort, filter_type)
        print(f"  {description}: {url}")
    
    # 测试参数验证
    print("\n--- 测试参数验证 ---")
    print(f"  有效排序参数 'saved': {module.validate_sort_parameter('saved')}")
    print(f"  无效排序参数 'invalid': {module.validate_sort_parameter('invalid')}")
    print(f"  有效过滤器参数 'chinese_subtitle': {module.validate_filter_parameter('chinese_subtitle')}")
    print(f"  无效过滤器参数 'invalid': {module.validate_filter_parameter('invalid')}")
    
    # 测试名称获取
    print("\n--- 测试名称获取 ---")
    print(f"  排序选项: {module.get_available_sorts()}")
    print(f"  过滤器选项: {module.get_available_filters()}")
    
    print("\n✅ 排序与过滤器模块测试完成")


if __name__ == "__main__":
    test_sort_filter_module()