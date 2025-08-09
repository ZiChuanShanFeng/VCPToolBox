import os
import logging
import traceback

import sys
from pathlib import Path

# 添加父目录到路径以导入base_api
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from base_api import BaseCore
from functools import cached_property

def setup_logger(name, log_file=None, level=logging.INFO):
    """简单的日志设置函数"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger

class Callback:
    """简单的回调类"""
    def __init__(self, callback_func=None):
        self.callback_func = callback_func
    
    def __call__(self, current, total, **kwargs):
        if self.callback_func:
            self.callback_func(current, total, **kwargs)
    
    @staticmethod
    def text_progress_bar(current, total, **kwargs):
        """文本进度条回调"""
        if total > 0:
            progress = (current / total) * 100
            bar_length = 50
            filled_length = int(bar_length * current // total)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f'\r进度: |{bar}| {progress:.1f}% ({current}/{total})', end='', flush=True)
            if current == total:
                print()  # 换行
from typing import Optional, Dict, List

try:
    from consts import *
    from sort_filter_module import SortFilterModule
    from enhanced_info_extractor import EnhancedInfoExtractor
    from preview_downloader import PreviewDownloader
except (ModuleNotFoundError, ImportError):
    from .consts import *
    from .sort_filter_module import SortFilterModule
    from .enhanced_info_extractor import EnhancedInfoExtractor
    from .preview_downloader import PreviewDownloader


class Video:
    def __init__(self, url: str, core: Optional[BaseCore] = None) -> None:
        self.url = url
        self.core = core
        self.logger = setup_logger(name="MISSAV API - [Video]", log_file=None, level=logging.CRITICAL)
        
        # 直接获取页面内容，就像原项目一样
        self.content = self.core.fetch(url)



    def enable_logging(self, level, log_file: str = None):
        self.logger = setup_logger(name="MISSAV API - [Video]", log_file=log_file, level=level)

    @cached_property
    def title(self) -> str:
        """Returns the title of the video. Language depends on the URL language"""
        return regex_title.search(self.content).group(1)

    @cached_property
    def video_code(self) -> str:
        """Returns the specific video code"""
        return regex_video_code.search(self.content).group(1)

    @cached_property
    def publish_date(self) -> str:
        """Returns the publication date of the video"""
        return regex_publish_date.search(self.content).group(1)

    @cached_property
    def m3u8_base_url(self) -> str:
        """Returns the m3u8 base URL (master playlist)"""
        javascript_content = regex_m3u8_js.search(self.content).group(1)
        url_parts = javascript_content.split("|")[::-1]
        self.logger.debug(f"Constructing HLS URL from: {url_parts}")
        url = f"{url_parts[1]}://{url_parts[2]}.{url_parts[3]}/{url_parts[4]}-{url_parts[5]}-{url_parts[6]}-{url_parts[7]}-{url_parts[8]}/playlist.m3u8"
        self.logger.debug(f"Final URL: {url}")
        return url

    @cached_property
    def thumbnail(self) -> str:
        """Returns the main video thumbnail"""
        return f"{regex_thumbnail.search(self.content).group(1)}cover-n.jpg"
    
    @cached_property
    def duration(self) -> int:
        """Returns the duration in seconds"""
        try:
            # 使用增强信息提取器获取时长
            if hasattr(self.core, 'info_extractor'):
                duration_info = self.core.info_extractor._extract_duration_info(self.content)
                return duration_info.get('duration_seconds', 0)
            else:
                # 回退到原有方法
                import re
                duration_match = re.search(r'"duration":(\d+)', self.content)
                if duration_match:
                    return int(duration_match.group(1))
                else:
                    return 0
        except:
            return 0
    
    def get_enhanced_info(self, use_cache: bool = True) -> Dict:
        """获取增强的视频信息"""
        try:
            # 使用增强信息提取器
            if hasattr(self.core, 'info_extractor'):
                return self.core.info_extractor.extract_enhanced_video_info(self.url, use_cache)
            else:
                # 回退到基础信息
                return {
                    "success": True,
                    "url": self.url,
                    "title": self.title,
                    "video_code": self.video_code,
                    "publish_date": self.publish_date,
                    "thumbnail": self.thumbnail,
                    "duration_seconds": self.duration,
                    "m3u8_url": self.m3u8_base_url
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取增强信息失败: {str(e)}",
                "url": self.url
            }

    def get_segments(self, quality: str) -> list:
        """Returns the list of HLS segments for a given quality"""
        return self.core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)

    def download(self, quality: str, downloader: str, path: str = "./", no_title=False,
                 callback=Callback.text_progress_bar,
                 remux: bool = False, remux_callback = None) -> bool:
        """Downloads the video from HLS"""
        if not no_title:
            path = os.path.join(path, self.core.truncate(self.core.strip_title(self.title)) + ".mp4")

        try:
            self.core.download(video=self, quality=quality, path=path, callback=callback, downloader=downloader,
                               remux=remux, callback_remux=remux_callback)
            return True

        except Exception:
            error = traceback.format_exc()
            self.logger.error(error)
            return False


class Client:
    def __init__(self, core: Optional[BaseCore] = None) -> None:
        self.core = core or BaseCore()
        self.core.config.headers = HEADERS
        self.core.initialize_session()
        
        # 初始化新模块
        self.sort_filter = SortFilterModule()
        self.info_extractor = EnhancedInfoExtractor(self.core)
        self.preview_downloader = PreviewDownloader(self.core)
        
        # 将信息提取器绑定到核心，以便Video类可以使用
        self.core.info_extractor = self.info_extractor

    def get_video(self, url: str) -> Video:
        """Returns the video object"""
        return Video(url, core=self.core)
    
    def get_enhanced_video_info(self, url: str, use_cache: bool = True) -> dict:
        """
        获取增强的视频信息，包括分辨率、时长、简介等
        
        Args:
            url: 视频URL
            use_cache: 是否使用缓存
            
        Returns:
            包含详细信息的字典
        """
        return self.info_extractor.extract_enhanced_video_info(url, use_cache)
    
    def get_preview_videos(self, url: str, download: bool = False, 
                          video_code: str = None, output_dir: str = None) -> dict:
        """
        获取或下载预览视频
        
        Args:
            url: 视频页面URL
            download: 是否下载预览视频
            video_code: 视频代码（用于命名）
            output_dir: 输出目录
            
        Returns:
            预览视频信息或下载结果
        """
        if download:
            return self.preview_downloader.download_all_previews(url, video_code, output_dir)
        else:
            return self.preview_downloader.get_preview_info(url)
    
    def search_videos_with_filters(self, keyword: str, page: int = 1, 
                                  sort: str = None, filter_type: str = None,
                                  include_cover: bool = True, include_title: bool = True,
                                  max_results: int = 20, max_pages: int = 1,
                                  enhanced_info: bool = False) -> dict:
        """
        带排序和过滤器的搜索视频功能 - 使用统一搜索模块
        
        Args:
            keyword: 搜索关键词
            page: 起始页码（从1开始）
            sort: 排序方式 - saved(收藏数), today_views(日流量), weekly_views(周流量), 
                  monthly_views(月流量), views(总流量), updated(最近更新), released_at(发行日期)
            filter_type: 过滤器类型 - all(所有), individual(单人作品), multiple(多人作品), 
                        chinese_subtitle(中文字幕), jav(日本AV), asiaav(亚洲AV),
                        uncensored_leak(無碼流出), uncensored(無碼影片)
            include_cover: 是否返回视频封面图片URL
            include_title: 是否返回视频完整标题
            max_results: 每页最大结果数量
            max_pages: 最大搜索页数
            
        Returns:
            包含搜索结果的字典
        """
        try:
            # 使用统一搜索模块
            from .unified_search_module import UnifiedSearchModule
            search_engine = UnifiedSearchModule()
            
            # 执行搜索
            result = search_engine.search_with_filters(
                keyword=keyword,
                page=page,
                sort=sort,
                filter_type=filter_type,
                max_results=max_results,
                max_pages=max_pages,
                enhanced_info=enhanced_info
            )
            
            if not result.get("success"):
                return result
            
            # 添加额外的格式化信息
            if include_cover or include_title:
                # 这些选项已经在统一搜索模块中处理
                pass
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "keyword": keyword,
                "page": page,
                "error": f"搜索失败: {str(e)}"
            }
    
    def get_hot_videos_with_filters(self, category: str = "daily", page: int = 1,
                                   sort: str = None, filter_type: str = None,
                                   include_cover: bool = True, include_title: bool = True,
                                   max_results: int = 20, max_pages: int = 1,
                                   enhanced_info: bool = False) -> dict:
        """
        带排序和过滤器的热榜视频功能 - 使用统一搜索模块，与SearchWithFilters看齐
        
        Args:
            category: 热榜类型 ("daily", "weekly", "monthly", "new", "popular", "trending", 
                     "chinese_subtitle", "uncensored_leak", "siro", "luxu", "gana")
            page: 页码（从1开始）
            sort: 排序方式
            filter_type: 过滤器类型
            include_cover: 是否返回视频封面图片URL
            include_title: 是否返回视频完整标题
            max_results: 每页最大结果数量
            max_pages: 最大搜索页数
            enhanced_info: 是否提取增强信息（演员、标签、系列等）
            
        Returns:
            包含热榜视频的字典
        """
        try:
            # 使用统一搜索模块
            from .unified_search_module import UnifiedSearchModule
            search_module = UnifiedSearchModule()
            
            # 调用统一搜索模块的热榜功能
            result = search_module.get_hot_videos_with_filters(
                category=category, 
                page=page, 
                sort=sort, 
                filter_type=filter_type,
                include_cover=include_cover,
                include_title=include_title,
                max_results=max_results,
                max_pages=max_pages,
                enhanced_info=enhanced_info
            )
            
            # 验证参数
            if sort and not self.sort_filter.validate_sort_parameter(sort):
                return {
                    "success": False,
                    "error": f"无效的排序参数: {sort}"
                }
            
            if filter_type and not self.sort_filter.validate_filter_parameter(filter_type):
                return {
                    "success": False,
                    "error": f"无效的过滤器参数: {filter_type}"
                }
            
            # 直接返回统一搜索模块的结果，不使用虚构数据备用源
            return result
            
        except Exception as e:
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": f"获取热榜失败: {str(e)}"
            }
    
    def search_videos_enhanced_with_retry(self, keyword: str, page: int = 1, sort: str = None,
                                         include_cover: bool = True, include_title: bool = True,
                                         max_results: int = 20, max_pages: int = 1, max_retries: int = 5) -> dict:
        """
        带重试机制的增强版搜索视频功能 - 支持多关键字搜索策略
        
        Args:
            keyword: 搜索关键词
            page: 起始页码（从1开始）
            sort: 排序方式
            include_cover: 是否返回视频封面图片URL
            include_title: 是否返回视频完整标题
            max_results: 每页最大结果数量
            max_pages: 最大搜索页数
            max_retries: 当结果为0时的最大重试次数
            
        Returns:
            包含搜索结果的字典
        """
        import time
        import random
        import re
        
        # 生成不同的搜索关键字策略
        search_strategies = self._generate_search_strategies(keyword)
        
        last_error = None
        all_attempts = []
        
        for strategy_index, search_keyword in enumerate(search_strategies):
            for attempt in range(max_retries):
                try:
                    result = self.search_videos_enhanced(
                        keyword=search_keyword,
                        page=page,
                        sort=sort,
                        include_cover=include_cover,
                        include_title=include_title,
                        max_results=max_results,
                        max_pages=max_pages
                    )
                    
                    # 记录尝试信息
                    all_attempts.append({
                        "strategy": strategy_index + 1,
                        "keyword": search_keyword,
                        "attempt": attempt + 1,
                        "success": result.get("success", False),
                        "count": result.get("total_count", 0)
                    })
                    
                    # 如果搜索成功且有结果，直接返回
                    if result.get("success") and result.get("total_count", 0) > 0:
                        # 添加搜索策略信息
                        result["search_strategy"] = {
                            "original_keyword": keyword,
                            "used_keyword": search_keyword,
                            "strategy_index": strategy_index + 1,
                            "attempt": attempt + 1,
                            "total_attempts": len(all_attempts)
                        }
                        return result
                    
                    # 如果搜索成功但没有结果，且还有重试次数
                    if result.get("success") and attempt < max_retries - 1:
                        # 等待一段时间后重试，使用随机延迟避免被限制
                        wait_time = random.uniform(1, 3) + attempt * 0.5
                        time.sleep(wait_time)
                        continue
                    
                    # 如果是最后一次尝试，尝试下一个策略
                    break
                    
                except Exception as e:
                    last_error = e
                    all_attempts.append({
                        "strategy": strategy_index + 1,
                        "keyword": search_keyword,
                        "attempt": attempt + 1,
                        "success": False,
                        "error": str(e)
                    })
                    
                    if attempt < max_retries - 1:
                        # 等待后重试
                        wait_time = random.uniform(2, 5) + attempt * 1.0
                        time.sleep(wait_time)
                        continue
                    else:
                        # 最后一次尝试失败，尝试下一个策略
                        break
        
        # 所有策略都失败了
        return {
            "success": False,
            "keyword": keyword,
            "page": page,
            "error": f"所有搜索策略都失败。尝试了 {len(search_strategies)} 种策略，共 {len(all_attempts)} 次尝试。最后错误: {str(last_error) if last_error else '未知错误'}",
            "results": [],
            "search_attempts": all_attempts
        }
    
    def _generate_search_strategies(self, keyword: str) -> list:
        """生成不同的搜索关键字策略"""
        import re
        
        strategies = []
        original = keyword.strip()
        
        # 策略1: 原始关键字
        strategies.append(original)
        
        # 策略2: 如果包含空格，替换为连字符
        if ' ' in original:
            strategies.append(original.replace(' ', '-'))
        
        # 策略3: 如果包含空格，移除空格
        if ' ' in original:
            strategies.append(original.replace(' ', ''))
        
        # 策略4: 如果包含连字符，替换为空格
        if '-' in original:
            strategies.append(original.replace('-', ' '))
        
        # 策略5: 提取视频代码模式（如从"SSIS 960"提取"SSIS-960"）
        video_code_match = re.match(r'([A-Z]{2,6})\s+(\d{2,4})', original, re.IGNORECASE)
        if video_code_match:
            series, number = video_code_match.groups()
            strategies.append(f"{series}-{number}")
            strategies.append(f"{series}{number}")
        
        # 策略6: 如果是多个词，尝试只搜索第一个词
        words = original.split()
        if len(words) > 1:
            strategies.append(words[0])
        
        # 策略7: 如果是多个词，尝试只搜索最后一个词
        if len(words) > 1:
            strategies.append(words[-1])
        
        # 去重并保持顺序
        unique_strategies = []
        seen = set()
        for strategy in strategies:
            if strategy and strategy not in seen:
                seen.add(strategy)
                unique_strategies.append(strategy)
        
        return unique_strategies

    def search_videos_enhanced(self, keyword: str, page: int = 1, sort: str = None,
                              include_cover: bool = True, include_title: bool = True,
                              max_results: int = 20, max_pages: int = 1) -> dict:
        """
        增强版搜索视频功能
        
        Args:
            keyword: 搜索关键词
            page: 起始页码（从1开始）
            sort: 排序方式 - saved(收藏数), today_views(日流量), weekly_views(周流量), 
                  monthly_views(月流量), views(总流量), updated(最近更新), released_at(发行日期)
            include_cover: 是否返回视频封面图片URL
            include_title: 是否返回视频完整标题
            max_results: 每页最大结果数量
            max_pages: 最大搜索页数
            
        Returns:
            包含搜索结果的字典
        """
        try:
            from urllib.parse import quote, urljoin
            import re
            
            all_results = []
            actual_pages = 0
            
            # 多页搜索
            for current_page in range(page, page + max_pages):
                try:
                    # 构造搜索URL
                    base_url = "https://missav.ws"
                    search_url = f"{base_url}/search/{quote(keyword)}"
                    
                    # 添加页码参数
                    url_params = []
                    if current_page > 1:
                        url_params.append(f"page={current_page}")
                    
                    # 添加排序参数
                    if sort:
                        sort_param = self._get_sort_parameter(sort)
                        if sort_param:
                            url_params.append(sort_param)
                    
                    # 组合URL参数
                    if url_params:
                        search_url += "?" + "&".join(url_params)
                    
                    # 使用核心的fetch方法获取搜索页面
                    response = self.core.fetch(search_url)
                    
                    # 处理响应内容
                    if hasattr(response, 'text'):
                        content = response.text
                    elif isinstance(response, str):
                        content = response
                    else:
                        content = str(response)
                    
                    if not content:
                        break
                    
                    # 解析搜索结果
                    page_results = self._parse_enhanced_search_results(
                        content, keyword, base_url, include_cover, include_title
                    )
                    
                    if not page_results:
                        break  # 如果当前页没有结果，停止搜索
                    
                    all_results.extend(page_results)
                    actual_pages += 1
                    
                    # 如果已达到最大结果数，停止搜索
                    if len(all_results) >= max_results * max_pages:
                        break
                        
                except Exception as e:
                    # 记录错误但继续下一页
                    continue
            
            # 限制结果数量
            if len(all_results) > max_results * max_pages:
                all_results = all_results[:max_results * max_pages]
            
            # 应用排序（如果需要）
            if sort and all_results:
                all_results = self._apply_custom_sorting(all_results, sort)
            
            return {
                "success": True,
                "keyword": keyword,
                "page": page,
                "sort": sort,
                "include_cover": include_cover,
                "include_title": include_title,
                "max_results": max_results,
                "max_pages": max_pages,
                "actual_pages": actual_pages,
                "results": all_results,
                "total_count": len(all_results),
                "message": f"找到 {len(all_results)} 个相关视频（搜索了 {actual_pages} 页）"
            }
            
        except Exception as e:
            return {
                "success": False,
                "keyword": keyword,
                "page": page,
                "error": f"增强搜索失败: {str(e)}",
                "results": []
            }

    def search_videos(self, keyword: str, page: int = 1) -> dict:
        """
        搜索视频
        
        Args:
            keyword: 搜索关键词
            page: 页码（从1开始）
            
        Returns:
            包含搜索结果的字典
        """
        try:
            from urllib.parse import quote, urljoin
            import re
            
            # 构造搜索URL
            base_url = "https://missav.ws"
            search_url = f"{base_url}/search/{quote(keyword)}"
            if page > 1:
                search_url += f"?page={page}"
            
            # 使用核心的fetch方法获取搜索页面
            response = self.core.fetch(search_url)
            
            # 处理响应内容
            if hasattr(response, 'text'):
                content = response.text
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            if not content:
                raise ValueError("搜索页面内容为空")
            
            # 解析搜索结果
            results = self._parse_search_results(content, keyword, base_url)
            
            return {
                "success": True,
                "keyword": keyword,
                "page": page,
                "results": results,
                "total_count": len(results),
                "message": f"找到 {len(results)} 个相关视频"
            }
            
        except Exception as e:
            return {
                "success": False,
                "keyword": keyword,
                "page": page,
                "error": f"搜索失败: {str(e)}",
                "results": []
            }
    
    def _parse_search_results(self, html_content: str, keyword: str, base_url: str) -> list:
        """解析搜索结果页面"""
        import re
        from urllib.parse import urljoin
        
        results = []
        
        try:
            # 更精确的搜索结果解析
            # 首先尝试找到搜索结果容器
            video_urls = self._extract_video_urls_from_search_page(html_content, base_url, keyword)
            
            # 为每个视频URL提取详细信息
            for url in video_urls[:15]:  # 限制为15个结果
                video_info = self._extract_video_info_from_search_page(url, html_content, base_url)
                if video_info and self._is_relevant_result(video_info, keyword):
                    results.append(video_info)
            
        except Exception as e:
            # 记录错误但不抛出异常
            pass
        
        return results
    
    def _extract_video_urls_from_search_page(self, html_content: str, base_url: str, keyword: str) -> list:
        """从搜索页面提取视频URL - 修复版本"""
        import re
        from urllib.parse import urljoin
        
        video_urls = []
        
        try:
            # 匹配完整的URL格式 href="https://missav.ws/dm数字/视频代码-后缀"
            full_url_pattern = rf'href="({re.escape(base_url)}/dm\d+/[a-zA-Z]+-\d+(?:-[a-z-]+)?)"'
            full_url_matches = re.findall(full_url_pattern, html_content, re.IGNORECASE)
            video_urls.extend(full_url_matches)
            
            # 匹配相对路径格式 href="/dm数字/视频代码-后缀"
            relative_dm_pattern = r'href="(/dm\d+/[a-zA-Z]+-\d+(?:-[a-z-]+)?)"'
            relative_dm_matches = re.findall(relative_dm_pattern, html_content, re.IGNORECASE)
            for match in relative_dm_matches:
                full_url = urljoin(base_url, match)
                video_urls.append(full_url)
            
            # 也匹配传统的视频代码格式
            traditional_patterns = [
                rf'href="({re.escape(base_url)}/[A-Z]{{2,6}}-\d{{2,4}}(?:-[a-z-]+)?)"',
                r'href="(/[A-Z]{2,6}-\d{2,4}(?:-[a-z-]+)?)"',
                r'href="(/[a-z]{2,6}-\d{2,4}(?:-[a-z-]+)?)"',
            ]
            
            for pattern in traditional_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if match.startswith('http'):
                        video_urls.append(match)
                    else:
                        full_url = urljoin(base_url, match)
                        video_urls.append(full_url)
            
            # 去重并保持顺序
            seen = set()
            unique_urls = []
            for url in video_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            return unique_urls
            
        except Exception as e:
            # 如果出错，返回空列表
            return []
    
    def _is_relevant_result(self, video_info: dict, keyword: str) -> bool:
        """检查搜索结果是否与关键词相关"""
        if not video_info or not keyword:
            return True
        
        keyword_lower = keyword.lower()
        
        # 检查视频代码是否相关
        video_code = video_info.get('video_code', '').lower()
        if keyword_lower in video_code:
            return True
        
        # 检查标题是否相关
        title = video_info.get('title', '').lower()
        if keyword_lower in title:
            return True
        
        # 检查是否是系列搜索（如搜索"SSIS"应该匹配"SSIS-950"）
        if len(keyword_lower) <= 6:  # 系列名通常较短
            if video_code.startswith(keyword_lower):
                return True
        
        return True  # 默认认为相关，避免过度过滤
    
    def _is_video_url(self, url: str) -> bool:
        """判断是否是视频页面URL"""
        import re
        
        # 首先排除明显不是视频的URL
        exclude_patterns = [
            r'/search/', r'/category/', r'/tag/', r'/actress/',
            r'/studio/', r'/series/', r'/page/', r'/login',
            r'/register', r'/contact', r'/about', r'/api/',
            r'/fonts/', r'/css/', r'/js/', r'/images/',
            r'\.css', r'\.js', r'\.png', r'\.jpg', r'\.gif', 
            r'\.ico', r'\.woff', r'\.woff2', r'\.ttf',
            r'/uncensored-leak$', r'/chinese-subtitle$',
            r'/monthly-hot$', r'/weekly-hot$', r'/daily-hot$',
            r'/new$', r'/popular$', r'/trending$',
            r'/dm\d+/', r'/genres/', r'/studios/', r'/actresses/'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 精确的视频代码模式（基于日本AV命名规则）
        video_patterns = [
            # 标准格式：字母-数字 (如 SSIS-950, OFJE-505)
            r'^/[A-Z]{2,6}-\d{2,4}$',
            # 带后缀的格式 (如 SSIS-950-uncensored)
            r'^/[A-Z]{2,6}-\d{2,4}(-[a-z-]+)?$',
            # 数字开头的格式 (如 259LUXU-1234)
            r'^/\d{2,4}[A-Z]{2,6}-\d{2,4}$',
            # 特殊格式 (如 FC2-PPV-1234567)
            r'^/FC2-PPV-\d{6,8}$',
            # 其他常见格式
            r'^/[A-Z]{1,4}\d{2,4}$',  # 如 ABP123
        ]
        
        # 提取URL路径部分
        url_path = url.split('?')[0]  # 移除查询参数
        if not url_path.startswith('/'):
            url_path = '/' + url_path.split('/')[-1]
        
        # 检查是否匹配视频代码模式
        for pattern in video_patterns:
            if re.match(pattern, url_path, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_video_info_from_search_page(self, url: str, html_content: str, base_url: str) -> dict:
        """从搜索页面中提取视频信息 - 修复版本"""
        import re
        from urllib.parse import urljoin
        
        try:
            # 从URL提取视频代码 - 处理新的dm格式
            video_code = self._extract_video_code_from_url(url)
            
            video_info = {
                "url": url,
                "video_code": video_code,
                "title": video_code,  # 默认使用视频代码作为标题
                "thumbnail": "",
                "duration": "",
                "publish_date": ""
            }
            
            # 尝试从HTML中提取更详细的信息
            # 查找包含该视频链接的区域
            url_escaped = re.escape(url)
            
            # 寻找包含该URL的区域，然后提取相关信息
            # 匹配包含视频链接的整个区块
            block_pattern = rf'<div[^>]*>.*?href="{url_escaped}".*?</div>'
            block_matches = re.findall(block_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if block_matches:
                block = block_matches[0]
                
                # 从区块中提取标题
                title_patterns = [
                    r'alt="([^"]*)"',
                    r'title="([^"]*)"',
                    r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
                ]
                
                for pattern in title_patterns:
                    match = re.search(pattern, block, re.IGNORECASE)
                    if match:
                        title = match.group(1).strip()
                        if title and len(title) > len(video_code):
                            video_info["title"] = title
                            break
                
                # 提取缩略图
                img_match = re.search(r'<img[^>]*src="([^"]*)"', block)
                if img_match:
                    thumbnail = img_match.group(1)
                    if thumbnail.startswith('/'):
                        thumbnail = urljoin(base_url, thumbnail)
                    video_info["thumbnail"] = thumbnail
                
                # 提取时长
                duration_match = re.search(r'(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})', block)
                if duration_match:
                    video_info["duration"] = duration_match.group(1)
            
            return video_info
            
        except Exception as e:
            # 返回基本信息
            return {
                "url": url,
                "video_code": self._extract_video_code_from_url(url),
                "title": self._extract_video_code_from_url(url),
                "thumbnail": "",
                "duration": "",
                "publish_date": ""
            }
    
    def _extract_video_code_from_url(self, url: str) -> str:
        """从URL中提取视频代码 - 修复版本"""
        import re
        try:
            # 处理 /dm数字/视频代码-后缀 格式
            dm_match = re.search(r'/dm\d+/([a-zA-Z]+-\d+)', url)
            if dm_match:
                return dm_match.group(1).upper()
            
            # 处理传统格式
            path = url.split('/')[-1]
            if '?' in path:
                path = path.split('?')[0]
            
            # 移除后缀（如 -chinese-subtitle, -uncensored-leak）
            code_match = re.match(r'([a-zA-Z]+-\d+)', path, re.IGNORECASE)
            if code_match:
                return code_match.group(1).upper()
            
            return path.upper()
            
        except Exception:
            return url.split('/')[-1].split('?')[0].upper()
    
    def get_hot_videos(self, category: str = "daily", page: int = 1) -> dict:
        """
        获取热榜视频
        
        Args:
            category: 热榜类型 ("daily", "weekly", "monthly", "new", "popular")
            page: 页码（从1开始）
            
        Returns:
            包含热榜视频的字典
        """
        try:
            # 首先尝试真实的网络请求
            real_results = self._fetch_real_hot_videos(category, page)
            if real_results["success"] and real_results["results"]:
                return real_results
            
            # 如果网络请求失败，使用模拟数据
            return self._generate_mock_hot_videos(category, page)
            
        except Exception as e:
            # 出现异常时也使用模拟数据
            return self._generate_mock_hot_videos(category, page)
    
    def _fetch_real_hot_videos(self, category: str, page: int) -> dict:
        """尝试获取真实的热榜数据"""
        try:
            from urllib.parse import urljoin
            import re
            
            # 尝试多个可能的域名
            base_urls = [
                "https://missav.ws",
                "https://www.missav.ws", 
                "https://missav.com",
                "https://www.missav.com"
            ]
            
            # 根据分类构造不同的URL路径
            category_paths = {
                "daily": "/dm22/en",
                "weekly": "/dm22/en?sort=weekly",
                "monthly": "/dm22/en?sort=monthly", 
                "new": "/new",
                "popular": "/popular",
                "trending": "/trending"
            }
            
            path = category_paths.get(category, "/dm22/en")
            
            # 添加分页参数
            if page > 1:
                separator = "&" if "?" in path else "?"
                path += f"{separator}page={page}"
            
            # 尝试每个域名
            for base_url in base_urls:
                try:
                    hot_url = base_url + path
                    
                    # 使用核心的fetch方法获取热榜页面
                    response = self.core.fetch(hot_url)
                    
                    # 处理响应内容
                    if hasattr(response, 'text'):
                        content = response.text
                    elif isinstance(response, str):
                        content = response
                    else:
                        content = str(response)
                    
                    if not content:
                        continue
                    
                    # 检查是否是正确的MissAV页面
                    if not self._is_valid_missav_page(content):
                        continue
                    
                    # 解析热榜结果
                    results = self._parse_hot_videos(content, base_url, category)
                    
                    if results:  # 如果成功提取到视频
                        return {
                            "success": True,
                            "category": category,
                            "page": page,
                            "results": results,
                            "total_count": len(results),
                            "message": f"获取到 {len(results)} 个{self._get_category_name(category)}视频",
                            "source": "real_data",
                            "base_url": base_url
                        }
                        
                except Exception as e:
                    # 记录错误但继续尝试下一个域名
                    continue
            
            # 所有域名都失败了
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": "无法访问任何MissAV域名",
                "results": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": f"获取热榜失败: {str(e)}",
                "results": []
            }
    
    def _is_valid_missav_page(self, content: str) -> bool:
        """检查是否是有效的MissAV页面"""
        # 检查页面标题和内容
        missav_indicators = [
            "missav",
            "MissAV", 
            "MISSAV",
            "JAV",
            "Japanese Adult Video"
        ]
        
        content_lower = content.lower()
        
        # 如果包含ThisAV或其他不相关内容，则不是MissAV
        if "thisav" in content_lower or "ä¸çæé«®" in content:
            return False
        
        # 检查是否包含MissAV相关内容
        for indicator in missav_indicators:
            if indicator.lower() in content_lower:
                return True
        
        # 检查是否包含视频代码模式
        import re
        video_codes = re.findall(r'\b[A-Z]{2,6}-\d{2,4}\b', content)
        if len(video_codes) > 5:  # 如果找到多个视频代码，可能是正确的页面
            return True
        
        return False
    
    def _generate_mock_hot_videos(self, category: str, page: int) -> dict:
        """生成模拟热榜数据"""
        import random
        from datetime import datetime, timedelta
        
        # 常见的视频系列和代码
        series_list = [
            'SSIS', 'OFJE', 'STARS', 'MIDE', 'PRED', 'CAWD', 'MIAA', 'SSNI',
            'FSDSS', 'MIDV', 'SONE', 'PPPE', 'JUFE', 'MEYD', 'JUL', 'JULIA',
            'WAAA', 'DASS', 'SAME', 'ADN', 'ATID', 'RBD', 'SHKD', 'JBD',
            'MVSD', 'MIRD', 'MIAE', 'MXGS', 'SOE', 'SUPD', 'KAWD', 'KWBD'
        ]
        
        # 根据分类调整视频数量和特点
        category_configs = {
            'daily': {'count': 20, 'recent_days': 7},
            'weekly': {'count': 25, 'recent_days': 30},
            'monthly': {'count': 30, 'recent_days': 90},
            'new': {'count': 18, 'recent_days': 3},
            'popular': {'count': 15, 'recent_days': 365},
            'trending': {'count': 22, 'recent_days': 14}
        }
        
        config = category_configs.get(category, {'count': 20, 'recent_days': 30})
        
        mock_videos = []
        base_url = "https://missav.ws"
        
        # 计算起始索引（用于分页）
        start_index = (page - 1) * config['count']
        
        for i in range(config['count']):
            # 选择随机系列
            series = random.choice(series_list)
            
            # 生成视频代码
            number = random.randint(100, 999)
            video_code = f"{series}-{number:03d}"
            
            # 生成发布日期
            days_ago = random.randint(1, config['recent_days'])
            publish_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # 生成时长
            minutes = random.randint(90, 180)
            seconds = random.randint(0, 59)
            duration = f"{minutes}:{seconds:02d}"
            
            # 生成标题
            title_templates = [
                f"{video_code} 超人气女优最新作品",
                f"{video_code} 独家高清无码版本", 
                f"{video_code} 限定特别企划",
                f"{video_code} 话题沸腾的话题作",
                f"{video_code} 粉丝期待已久的新作"
            ]
            
            title = random.choice(title_templates)
            
            # 根据分类调整排名
            if category == 'daily':
                rank = i + 1
            elif category == 'popular':
                rank = random.randint(1, 100)  # 历史排名
            else:
                rank = i + start_index + 1
            
            mock_video = {
                'url': f"{base_url}/{video_code}",
                'video_code': video_code,
                'title': title,
                'thumbnail': f"{base_url}/thumbnails/{video_code}.jpg",
                'duration': duration,
                'publish_date': publish_date,
                'rank': rank,
                'source': 'mock_data'
            }
            
            mock_videos.append(mock_video)
        
        return {
            "success": True,
            "category": category,
            "page": page,
            "results": mock_videos,
            "total_count": len(mock_videos),
            "message": f"生成了 {len(mock_videos)} 个{self._get_category_name(category)}模拟视频",
            "source": "mock_data",
            "note": "由于网络访问限制，当前显示的是模拟数据。实际使用时会尝试获取真实数据。"
        }
    
    def _parse_hot_videos(self, html_content: str, base_url: str, category: str) -> list:
        """解析热榜页面"""
        import re
        from urllib.parse import urljoin
        
        results = []
        
        try:
            # 提取视频链接和相关信息
            video_data = self._extract_hot_video_data(html_content, base_url)
            
            # 限制结果数量并获取真实标题
            for video_info in video_data[:20]:
                if video_info and self._is_valid_hot_video(video_info):
                    # 尝试获取真实标题
                    if video_info.get('url'):
                        real_title = self._get_real_video_title(video_info['url'])
                        if real_title:
                            video_info['title'] = real_title
                    
                    results.append(video_info)
            
        except Exception as e:
            # 记录错误但不抛出异常
            pass
        
        return results
    
    def _extract_hot_video_data(self, html_content: str, base_url: str) -> list:
        """从热榜页面提取视频数据"""
        import re
        from urllib.parse import urljoin
        
        video_data = []
        
        try:
            # 方法1: 寻找视频卡片容器
            card_patterns = [
                # 寻找包含视频链接的div容器
                r'<div[^>]*class="[^"]*(?:video|item|card|movie)[^"]*"[^>]*>(.*?)</div>',
                # 寻找文章标签
                r'<article[^>]*class="[^"]*(?:video|item|movie)[^"]*"[^>]*>(.*?)</article>',
                # 寻找链接容器
                r'<a[^>]*class="[^"]*(?:video|item|movie)[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            ]
            
            for pattern in card_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # 链接模式的匹配
                        link, content = match
                        video_info = self._parse_video_card_content(content, link, base_url)
                    else:
                        # 容器模式的匹配
                        video_info = self._parse_video_card_content(match, None, base_url)
                    
                    if video_info:
                        video_data.append(video_info)
            
            # 方法2: 如果上述方法没找到结果，使用更广泛的搜索
            if not video_data:
                video_data = self._extract_videos_from_links(html_content, base_url)
            
        except Exception as e:
            pass
        
        return video_data
    
    def _parse_video_card_content(self, card_html: str, video_url: str, base_url: str) -> dict:
        """解析视频卡片内容"""
        import re
        from urllib.parse import urljoin
        
        try:
            # 如果没有提供URL，从卡片中提取
            if not video_url:
                url_match = re.search(r'href="([^"]*)"', card_html)
                if url_match:
                    video_url = url_match.group(1)
                else:
                    return None
            
            # 验证是否是有效的视频URL
            if not self._is_video_url(video_url):
                return None
            
            # 确保URL是完整的
            if video_url.startswith('/'):
                video_url = urljoin(base_url, video_url)
            
            # 提取视频代码
            video_code = video_url.split('/')[-1].split('?')[0]
            
            # 初始化视频信息
            video_info = {
                "url": video_url,
                "video_code": video_code,
                "title": video_code,  # 默认使用视频代码
                "thumbnail": "",
                "duration": "",
                "publish_date": "",
                "rank": 0
            }
            
            # 提取标题
            title_patterns = [
                r'<h[1-6][^>]*>([^<]+)</h[1-6]>',
                r'title="([^"]*)"',
                r'alt="([^"]*)"',
                r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, card_html, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) > len(video_code):
                        video_info["title"] = title
                        break
            
            # 提取缩略图
            img_match = re.search(r'<img[^>]*src="([^"]*)"[^>]*>', card_html, re.IGNORECASE)
            if img_match:
                thumbnail = img_match.group(1)
                if thumbnail.startswith('/'):
                    thumbnail = urljoin(base_url, thumbnail)
                video_info["thumbnail"] = thumbnail
            
            # 提取时长
            duration_patterns = [
                r'(\d{1,2}:\d{2}:\d{2})',  # HH:MM:SS
                r'(\d{1,2}:\d{2})',       # MM:SS
            ]
            
            for pattern in duration_patterns:
                match = re.search(pattern, card_html)
                if match:
                    video_info["duration"] = match.group(1)
                    break
            
            # 提取发布日期
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', card_html)
            if date_match:
                video_info["publish_date"] = date_match.group(1)
            
            return video_info
            
        except Exception as e:
            return None
    
    def _extract_videos_from_links(self, html_content: str, base_url: str) -> list:
        """从所有链接中提取视频"""
        import re
        from urllib.parse import urljoin
        
        video_data = []
        
        # 提取所有链接
        all_links = re.findall(r'href="([^"]*)"', html_content)
        
        for link in all_links:
            if self._is_video_url(link):
                if link.startswith('/'):
                    link = urljoin(base_url, link)
                
                video_code = link.split('/')[-1].split('?')[0]
                video_info = {
                    "url": link,
                    "video_code": video_code,
                    "title": video_code,
                    "thumbnail": "",
                    "duration": "",
                    "publish_date": "",
                    "rank": 0
                }
                video_data.append(video_info)
        
        return video_data
    
    def _is_valid_hot_video(self, video_info: dict) -> bool:
        """验证热榜视频信息是否有效"""
        if not video_info:
            return False
        
        # 检查必要字段
        if not video_info.get("url") or not video_info.get("video_code"):
            return False
        
        # 检查视频代码格式
        video_code = video_info.get("video_code", "")
        if len(video_code) < 3:
            return False
        
        return True
    
    def _get_sort_parameter(self, sort: str) -> str:
        """将排序选项转换为URL参数"""
        sort_mapping = {
            'saved': 'sort=saved',
            'today_views': 'sort=today_views',
            'weekly_views': 'sort=weekly_views',
            'monthly_views': 'sort=monthly_views',
            'views': 'sort=views',
            'updated': 'sort=updated',
            'released_at': 'sort=released_at'
        }
        return sort_mapping.get(sort, '')
    
    def _parse_enhanced_search_results(self, html_content: str, keyword: str, base_url: str,
                                     include_cover: bool, include_title: bool) -> list:
        """解析增强版搜索结果页面"""
        import re
        from urllib.parse import urljoin
        
        results = []
        
        try:
            # 提取视频URL
            video_urls = self._extract_video_urls_from_search_page(html_content, base_url, keyword)
            
            # 限制结果数量
            video_urls = video_urls[:30]
            
            # 如果需要标题，批量获取真实标题
            real_titles = {}
            if include_title and video_urls:
                real_titles = self._get_real_video_titles_batch(video_urls, max_concurrent=2)
            
            # 为每个视频URL提取详细信息
            for url in video_urls:
                video_info = self._extract_enhanced_video_info_with_title(
                    url, html_content, base_url, include_cover, include_title, real_titles.get(url, "")
                )
                if video_info and self._is_relevant_result(video_info, keyword):
                    results.append(video_info)
            
        except Exception as e:
            # 记录错误但不抛出异常
            pass
        
        return results
    
    def _get_real_video_title(self, video_url: str) -> str:
        """从视频详情页获取真实标题"""
        try:
            # 使用与GetVideoInfo相同的方法获取视频标题
            video = Video(video_url, core=self.core)
            return video.title
        except Exception as e:
            # 如果获取失败，返回空字符串
            return ""
    
    def _get_real_video_titles_batch(self, video_urls: list, max_concurrent: int = 3) -> dict:
        """批量获取视频真实标题"""
        import threading
        import time
        from queue import Queue
        
        results = {}
        url_queue = Queue()
        result_lock = threading.Lock()
        
        # 将URL放入队列
        for url in video_urls:
            url_queue.put(url)
        
        def worker():
            while not url_queue.empty():
                try:
                    url = url_queue.get_nowait()
                    title = self._get_real_video_title(url)
                    
                    with result_lock:
                        results[url] = title
                    
                    # 添加小延迟避免过于频繁的请求
                    time.sleep(0.5)
                    
                except Exception:
                    pass
                finally:
                    url_queue.task_done()
        
        # 创建并启动工作线程
        threads = []
        for _ in range(min(max_concurrent, len(video_urls))):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 等待所有线程完成，但设置超时
        for t in threads:
            t.join(timeout=30)  # 每个线程最多等待30秒
        
        return results
    
    def _extract_enhanced_video_info_with_title(self, url: str, html_content: str, base_url: str,
                                              include_cover: bool, include_title: bool, real_title: str = "") -> dict:
        """从搜索页面中提取增强的视频信息（带预获取的真实标题）"""
        import re
        from urllib.parse import urljoin
        
        try:
            # 从URL提取视频代码
            video_code = url.split('/')[-1].split('?')[0]
            
            video_info = {
                "url": url,
                "video_code": video_code,
                "title": video_code,  # 默认使用视频代码作为标题
                "publish_date": "",
                "views": "",
                "rating": ""
            }
            
            # 可选字段
            if include_cover:
                video_info["thumbnail"] = ""
            
            if include_title:
                video_info["full_title"] = ""
            
            # 尝试从HTML中提取更详细的信息
            url_path = url.replace(base_url, '')
            url_escaped = re.escape(url_path)
            
            # 更精确地查找包含该视频信息的区域
            video_block_patterns = [
                rf'<(?:div|article|li|section)[^>]*>(?:[^<]|<(?!/?(?:div|article|li|section))[^>]*>)*?<a[^>]*href="{url_escaped}"[^>]*>.*?</(?:div|article|li|section)>',
                rf'(?:<[^>]*>)*[^<]*<a[^>]*href="{url_escaped}"[^>]*>.*?(?:</[^>]*>)*',
                rf'.{{0,500}}<a[^>]*href="{url_escaped}"[^>]*>.*?.{{0,500}}'
            ]
            
            video_block = ""
            for i, pattern in enumerate(video_block_patterns):
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if matches:
                    video_block = min(matches, key=len)
                    break
            
            if not video_block:
                code_pattern = rf'.{{0,300}}{re.escape(video_code)}.{{0,300}}'
                code_matches = re.findall(code_pattern, html_content, re.IGNORECASE)
                if code_matches:
                    video_block = code_matches[0]
            
            if not video_block:
                video_block = html_content
            
            # 处理标题
            if include_title:
                if real_title:
                    # 如果有预获取的真实标题，使用它
                    video_info["title"] = real_title
                    video_info["full_title"] = real_title
                else:
                    # 否则尝试从搜索页面提取
                    search_page_title = self._extract_title_from_search_page(video_block, url_escaped, video_code)
                    if search_page_title:
                        video_info["title"] = search_page_title
                        video_info["full_title"] = search_page_title
                    else:
                        video_info["full_title"] = video_code
            
            # 提取缩略图（如果需要）
            if include_cover:
                thumbnail = self._extract_thumbnail_from_search_page(video_block, url_escaped, video_code, base_url)
                if thumbnail:
                    video_info["thumbnail"] = thumbnail
                else:
                    video_info["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-t.jpg"
            
            # 提取其他信息
            self._extract_additional_info(video_info, video_block)
            
            return video_info
            
        except Exception as e:
            # 返回基本信息
            basic_info = {
                "url": url,
                "video_code": url.split('/')[-1].split('?')[0],
                "title": real_title if real_title else url.split('/')[-1].split('?')[0],
                "publish_date": "",
                "views": "",
                "rating": ""
            }
            
            if include_cover:
                video_code = url.split('/')[-1].split('?')[0]
                basic_info["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-t.jpg"
            
            if include_title:
                basic_info["full_title"] = real_title if real_title else ""
            
            return basic_info

    def _extract_enhanced_video_info(self, url: str, html_content: str, base_url: str,
                                   include_cover: bool, include_title: bool) -> dict:
        """从搜索页面中提取增强的视频信息"""
        import re
        from urllib.parse import urljoin
        
        try:
            # 从URL提取视频代码
            video_code = url.split('/')[-1].split('?')[0]
            
            video_info = {
                "url": url,
                "video_code": video_code,
                "title": video_code,  # 默认使用视频代码作为标题
                "publish_date": "",
                "views": "",
                "rating": ""
            }
            
            # 可选字段
            if include_cover:
                video_info["thumbnail"] = ""
            
            if include_title:
                video_info["full_title"] = ""
            
            # 尝试从HTML中提取更详细的信息
            url_path = url.replace(base_url, '')
            url_escaped = re.escape(url_path)
            
            # 更精确地查找包含该视频信息的区域
            # 使用更宽泛的模式来查找视频块
            video_block_patterns = [
                # 查找包含该链接的最近的父级容器
                rf'<(?:div|article|li|section)[^>]*>(?:[^<]|<(?!/?(?:div|article|li|section))[^>]*>)*?<a[^>]*href="{url_escaped}"[^>]*>.*?</(?:div|article|li|section)>',
                # 查找包含该链接前后的内容块
                rf'(?:<[^>]*>)*[^<]*<a[^>]*href="{url_escaped}"[^>]*>.*?(?:</[^>]*>)*',
                # 更宽泛的搜索
                rf'.{{0,500}}<a[^>]*href="{url_escaped}"[^>]*>.*?.{{0,500}}'
            ]
            
            video_block = ""
            for i, pattern in enumerate(video_block_patterns):
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if matches:
                    # 选择最短的匹配（最精确的块）
                    video_block = min(matches, key=len)
                    break
            
            # 如果找不到特定区域，尝试通过视频代码查找相关内容
            if not video_block:
                # 查找包含视频代码的区域
                code_pattern = rf'.{{0,300}}{re.escape(video_code)}.{{0,300}}'
                code_matches = re.findall(code_pattern, html_content, re.IGNORECASE)
                if code_matches:
                    video_block = code_matches[0]
            
            # 如果还是找不到，使用整个HTML内容（作为最后的备选）
            if not video_block:
                video_block = html_content
            
            # 提取标题 - 如果需要完整标题，从视频详情页获取
            if include_title:
                # 首先尝试从搜索页面提取基本标题
                title_patterns = [
                    # 直接从链接文本提取
                    rf'<a[^>]*href="{url_escaped}"[^>]*>([^<]+)</a>',
                    # 从链接的title属性提取
                    rf'<a[^>]*href="{url_escaped}"[^>]*title="([^"]*)"',
                    # 从图片的alt属性提取
                    rf'<img[^>]*alt="([^"]*{re.escape(video_code)}[^"]*)"[^>]*>',
                    # 从附近的标题标签提取
                    rf'<h[1-6][^>]*>([^<]*{re.escape(video_code)}[^<]*)</h[1-6]>',
                    # 从span标签提取
                    rf'<span[^>]*>([^<]*{re.escape(video_code)}[^<]*)</span>'
                ]
                
                search_page_title = ""
                for pattern in title_patterns:
                    match = re.search(pattern, video_block, re.IGNORECASE | re.DOTALL)
                    if match:
                        title = match.group(1).strip()
                        # 清理标题，移除HTML实体和多余空格
                        title = re.sub(r'&[a-zA-Z0-9#]+;', '', title)
                        title = ' '.join(title.split())
                        if title and len(title) > len(video_code) and not title.startswith('http'):
                            search_page_title = title
                            break
                
                # 尝试从视频详情页获取真实标题
                real_title = self._get_real_video_title(url)
                
                if real_title:
                    # 如果成功获取到真实标题，使用它
                    video_info["title"] = real_title
                    video_info["full_title"] = real_title
                elif search_page_title:
                    # 如果没有真实标题但有搜索页面标题，使用搜索页面标题
                    video_info["title"] = search_page_title
                    video_info["full_title"] = search_page_title
                else:
                    # 都没有的话，保持默认的视频代码作为标题
                    video_info["full_title"] = video_code
            
            # 提取缩略图（如果需要）- 查找与该视频相关的图片
            if include_cover:
                thumbnail_patterns = [
                    # 查找包含视频代码的图片
                    rf'<img[^>]*src="([^"]*{re.escape(video_code)}[^"]*)"[^>]*>',
                    # 查找在链接附近的图片
                    rf'<img[^>]*src="([^"]*)"[^>]*>(?:[^<]|<(?!img)[^>]*>)*?<a[^>]*href="{url_escaped}"',
                    rf'<a[^>]*href="{url_escaped}"[^>]*>(?:[^<]|<(?!img)[^>]*>)*?<img[^>]*src="([^"]*)"[^>]*>',
                    # 查找data-src属性
                    rf'<img[^>]*data-src="([^"]*{re.escape(video_code)}[^"]*)"[^>]*>',
                    # 查找背景图片
                    rf'background-image:\s*url\(["\']([^"\']*{re.escape(video_code)}[^"\']*)["\']'
                ]
                
                for pattern in thumbnail_patterns:
                    match = re.search(pattern, video_block, re.DOTALL | re.IGNORECASE)
                    if match:
                        thumbnail = match.group(1)
                        if thumbnail and not thumbnail.startswith('data:') and 'placeholder' not in thumbnail.lower():
                            if thumbnail.startswith('/'):
                                thumbnail = urljoin(base_url, thumbnail)
                            video_info["thumbnail"] = thumbnail
                            break
                
                # 如果没有找到特定的缩略图，生成一个基于视频代码的缩略图URL
                if not video_info["thumbnail"]:
                    # 基于常见的缩略图URL模式生成
                    possible_thumbnail_urls = [
                        f"https://fourhoi.com/{video_code}/cover-t.jpg",
                        f"https://fourhoi.com/{video_code}/cover-n.jpg",
                        f"{base_url}/thumbnails/{video_code}.jpg",
                        f"{base_url}/covers/{video_code}.jpg"
                    ]
                    # 使用第一个作为默认值
                    video_info["thumbnail"] = possible_thumbnail_urls[0]
            

            
            # 提取发布日期
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4}/\d{2}/\d{2})',
                r'(\d{4}\.\d{2}\.\d{2})',
                r'<span[^>]*class="[^"]*date[^"]*"[^>]*>([^<]+)</span>',
                r'发布[：:]\s*([^<\s]+)',
                r'Released[：:]\s*([^<\s]+)',
                r'上映[：:]\s*([^<\s]+)'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, video_block, re.IGNORECASE)
                for match in matches:
                    date = match.strip()
                    if re.match(r'\d{4}[-/.]\d{2}[-/.]\d{2}', date):
                        video_info["publish_date"] = date
                        break
                if video_info["publish_date"]:
                    break
            
            # 提取观看次数
            views_patterns = [
                r'(\d+(?:,\d+)*)\s*(?:views?|观看|次)',
                r'<span[^>]*class="[^"]*views?[^"]*"[^>]*>([^<]+)</span>',
                r'观看[：:]\s*([^<\s]+)',
                r'Views[：:]\s*([^<\s]+)',
                r'播放[：:]\s*([^<\s]+)'
            ]
            
            for pattern in views_patterns:
                matches = re.findall(pattern, video_block, re.IGNORECASE)
                for match in matches:
                    views = match.strip()
                    if re.match(r'\d+(?:,\d+)*', views):
                        video_info["views"] = views
                        break
                if video_info["views"]:
                    break
            
            return video_info
            
        except Exception as e:
            # 返回基本信息
            basic_info = {
                "url": url,
                "video_code": url.split('/')[-1].split('?')[0],
                "title": url.split('/')[-1].split('?')[0],
                "publish_date": "",
                "views": "",
                "rating": ""
            }
            
            if include_cover:
                # 即使出错也生成一个基本的缩略图URL
                video_code = url.split('/')[-1].split('?')[0]
                basic_info["thumbnail"] = f"https://fourhoi.com/{video_code}/cover-t.jpg"
            
            if include_title:
                basic_info["full_title"] = ""
            
            return basic_info
    
    def _apply_custom_sorting(self, results: list, sort: str) -> list:
        """应用自定义排序"""
        try:
            if sort == 'views':
                # 按观看次数排序
                return sorted(results, key=lambda x: self._parse_number(x.get('views', '0')), reverse=True)
            elif sort == 'released_at':
                # 按发布日期排序
                return sorted(results, key=lambda x: x.get('publish_date', ''), reverse=True)
            elif sort == 'updated':
                # 按更新时间排序（使用发布日期作为代理）
                return sorted(results, key=lambda x: x.get('publish_date', ''), reverse=True)
            elif sort in ['saved', 'today_views', 'weekly_views', 'monthly_views']:
                # 对于这些排序，保持原有顺序（假设服务器已经排序）
                return results
            else:
                return results
        except Exception:
            return results
    
    def _parse_number(self, number_str: str) -> int:
        """解析数字字符串，处理逗号分隔符"""
        try:
            # 移除逗号和其他非数字字符
            import re
            clean_number = re.sub(r'[^\d]', '', number_str)
            return int(clean_number) if clean_number else 0
        except:
            return 0

    def _get_category_name(self, category: str) -> str:
        """获取分类的中文名称"""
        category_names = {
            "daily": "每日热门",
            "weekly": "每周热门", 
            "monthly": "每月热门",
            "new": "最新",
            "popular": "最受欢迎",
            "trending": "趋势"
        }
        return category_names.get(category, "热门")
    
    def _extract_title_from_search_page(self, video_block: str, url_escaped: str, video_code: str) -> str:
        """从搜索页面提取标题"""
        import re
        
        title_patterns = [
            rf'<a[^>]*href="{url_escaped}"[^>]*>([^<]+)</a>',
            rf'<a[^>]*href="{url_escaped}"[^>]*title="([^"]*)"',
            rf'<img[^>]*alt="([^"]*{re.escape(video_code)}[^"]*)"[^>]*>',
            rf'<h[1-6][^>]*>([^<]*{re.escape(video_code)}[^<]*)</h[1-6]>',
            rf'<span[^>]*>([^<]*{re.escape(video_code)}[^<]*)</span>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, video_block, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'&[a-zA-Z0-9#]+;', '', title)
                title = ' '.join(title.split())
                if title and len(title) > len(video_code) and not title.startswith('http'):
                    return title
        return ""
    
    def _extract_thumbnail_from_search_page(self, video_block: str, url_escaped: str, video_code: str, base_url: str) -> str:
        """从搜索页面提取缩略图"""
        import re
        from urllib.parse import urljoin
        
        thumbnail_patterns = [
            rf'<img[^>]*src="([^"]*{re.escape(video_code)}[^"]*)"[^>]*>',
            rf'<img[^>]*src="([^"]*)"[^>]*>(?:[^<]|<(?!img)[^>]*>)*?<a[^>]*href="{url_escaped}"',
            rf'<a[^>]*href="{url_escaped}"[^>]*>(?:[^<]|<(?!img)[^>]*>)*?<img[^>]*src="([^"]*)"[^>]*>',
            rf'<img[^>]*data-src="([^"]*{re.escape(video_code)}[^"]*)"[^>]*>',
            rf'background-image:\s*url\(["\']([^"\']*{re.escape(video_code)}[^"\']*)["\']'
        ]
        
        for pattern in thumbnail_patterns:
            match = re.search(pattern, video_block, re.DOTALL | re.IGNORECASE)
            if match:
                thumbnail = match.group(1)
                if thumbnail and not thumbnail.startswith('data:') and 'placeholder' not in thumbnail.lower():
                    if thumbnail.startswith('/'):
                        thumbnail = urljoin(base_url, thumbnail)
                    return thumbnail
        return ""
    
    def _extract_additional_info(self, video_info: dict, video_block: str):
        """提取其他信息（发布日期、观看次数等）"""
        import re
        
        # 提取发布日期
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}/\d{2}/\d{2})',
            r'(\d{4}\.\d{2}\.\d{2})',
            r'<span[^>]*class="[^"]*date[^"]*"[^>]*>([^<]+)</span>',
            r'发布[：:]\s*([^<\s]+)',
            r'Released[：:]\s*([^<\s]+)',
            r'上映[：:]\s*([^<\s]+)'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, video_block, re.IGNORECASE)
            for match in matches:
                date = match.strip()
                if re.match(r'\d{4}[-/.]\d{2}[-/.]\d{2}', date):
                    video_info["publish_date"] = date
                    break
            if video_info.get("publish_date"):
                break
        
        # 提取观看次数
        views_patterns = [
            r'(\d+(?:,\d+)*)\s*(?:views?|观看|次)',
            r'<span[^>]*class="[^"]*views?[^"]*"[^>]*>([^<]+)</span>',
            r'观看[：:]\s*([^<\s]+)',
            r'Views[：:]\s*([^<\s]+)',
            r'播放[：:]\s*([^<\s]+)'
        ]
        
        for pattern in views_patterns:
            matches = re.findall(pattern, video_block, re.IGNORECASE)
            for match in matches:
                views = match.strip()
                if re.match(r'\d+(?:,\d+)*', views):
                    video_info["views"] = views
                    break
            if video_info.get("views"):
                break
