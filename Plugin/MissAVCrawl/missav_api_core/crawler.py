#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 爬虫核心模块
"""

import os
import sys
import traceback
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import logging

# 导入 missAV API 相关模块
def import_missav_api():
    """导入 missAV API 模块"""
    import_errors = []
    
    # 方法1: 尝试导入本地的 missAV API 模块（优先）
    try:
        current_dir = Path(__file__).parent
        parent_dir = current_dir.parent
        sys.path.insert(0, str(parent_dir))
        
        from missav_api_core.missav_api import Client
        from missav_api_core.missav_api import Callback
        return Client, Callback, f"本地missav_api_core模块: {current_dir}"
    except ImportError as e:
        import_errors.append(f"本地missav_api_core导入失败: {str(e)}")
    
    # 方法2: 尝试导入已安装的 missAV_api 包
    try:
        from missav_api import Client
        from base_api.modules.progress_bars import Callback
        return Client, Callback, "pip安装的missAV_api包"
    except ImportError as e:
        import_errors.append(f"pip包导入失败: {str(e)}")
    
    # 方法3: 尝试导入 eaf_base_api 和本地 missAV API
    try:
        from base_api import BaseCore
        from base_api.modules.progress_bars import Callback
        
        # 导入本地的 missAV API 代码
        current_dir = Path(__file__).parent
        
        if current_dir.exists():
            sys.path.insert(0, str(current_dir))
            from missav_api import Client
            return Client, Callback, f"本地源码导入: {current_dir}"
        else:
            raise ImportError(f"本地 missAV API 路径不存在: {current_dir}")
            
    except ImportError as e:
        import_errors.append(f"本地源码导入失败: {str(e)}")
    
    # 如果都失败了，抛出详细错误
    error_msg = "无法导入 missAV API 模块。尝试的方法:\n" + "\n".join(import_errors)
    raise ImportError(error_msg)


class MissAVCrawler:
    """MissAV 视频下载器"""
    
    def __init__(self):
        self.download_dir = os.getenv('MISSAV_DOWNLOAD_DIR', './downloads')
        self.quality = os.getenv('MISSAV_QUALITY', 'best')
        self.downloader = os.getenv('MISSAV_DOWNLOADER', 'threaded')
        self.proxy = os.getenv('MISSAV_PROXY', '')
        
        # 确保下载目录存在
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        # 尝试初始化 missAV 客户端
        self.client = None
        self.Client = None
        self.Callback = None
        
        try:
            self.Client, self.Callback, import_source = import_missav_api()
            
            # 静默初始化客户端，避免日志输出
            stdout_backup = sys.stdout
            stderr_backup = sys.stderr
            
            try:
                sys.stdout = StringIO()
                sys.stderr = StringIO()
                self.client = self.Client()
                
                # 检查客户端是否有新功能
                self.has_enhanced_features = (
                    hasattr(self.client, 'get_enhanced_video_info') and
                    hasattr(self.client, 'get_preview_videos') and
                    hasattr(self.client, 'search_videos_with_filters')
                )
                
            finally:
                sys.stdout = stdout_backup
                sys.stderr = stderr_backup
                
            self.import_info = f"成功导入 missAV API: {import_source}"
            if self.has_enhanced_features:
                self.import_info += " (包含增强功能)"
            self.api_available = True
        except Exception as e:
            self.import_info = f"导入 missAV API 失败: {str(e)}"
            self.api_available = False
            self.has_enhanced_features = False
    
    def get_video_info(self, url: str) -> dict:
        """获取视频信息"""
        if not self.api_available or not self.client:
            return {
                "success": False,
                "error": "missAV API 不可用，无法获取视频信息"
            }
            
        try:
            # 重定向stdout和stderr，避免任何输出干扰JSON响应
            stdout_backup = sys.stdout
            stderr_backup = sys.stderr
            
            try:
                # 将stdout和stderr重定向到StringIO，捕获所有输出
                sys.stdout = StringIO()
                sys.stderr = StringIO()
                
                video = self.client.get_video(url)
                
                info = {
                    "title": video.title,
                    "video_code": video.video_code,
                    "publish_date": video.publish_date,
                    "thumbnail": video.thumbnail,
                    "m3u8_url": video.m3u8_base_url,
                    "url": url
                }
                
            finally:
                # 恢复stdout和stderr
                sys.stdout = stdout_backup
                sys.stderr = stderr_backup
            
            return {
                "success": True,
                "info": info,
                "message": "成功获取视频信息"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取视频信息失败: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def silent_callback(self, current, total, speed=None):
        """静默的进度回调函数，不输出到stdout"""
        # 什么都不做，避免输出干扰JSON响应
        pass
    
    def search_videos(self, keyword: str, page: int = 1, sort: str = None, 
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
        """
        if not self.api_available or not self.client:
            return {
                "success": False,
                "keyword": keyword,
                "page": page,
                "error": "missAV API 不可用，无法搜索视频",
                "results": []
            }
            
        try:
            # 重定向stdout和stderr，避免任何输出干扰JSON响应
            stdout_backup = sys.stdout
            stderr_backup = sys.stderr
            
            try:
                # 将stdout和stderr重定向到StringIO，捕获所有输出
                sys.stdout = StringIO()
                sys.stderr = StringIO()
                
                # 使用增强版客户端搜索视频，带重试机制
                result = self.client.search_videos_enhanced_with_retry(
                    keyword=keyword, 
                    page=page, 
                    sort=sort,
                    include_cover=include_cover,
                    include_title=include_title,
                    max_results=max_results,
                    max_pages=max_pages
                )
                
            finally:
                # 恢复stdout和stderr
                sys.stdout = stdout_backup
                sys.stderr = stderr_backup
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "keyword": keyword,
                "page": page,
                "error": f"搜索视频失败: {str(e)}",
                "results": [],
                "traceback": traceback.format_exc()
            }
    
    def get_hot_videos(self, category: str = "daily", page: int = 1) -> dict:
        """获取热榜视频"""
        # 首先尝试使用本地热榜模块（更稳定）
        try:
            from .hot_videos import MissAVHotVideos
            hot_videos_module = MissAVHotVideos()
            result = hot_videos_module.get_hot_videos(category, page)
            if result.get("success"):
                return result
        except Exception:
            pass  # 如果本地模块失败，继续尝试网络请求
        
        # 如果本地模块不可用，尝试网络请求
        if not self.api_available or not self.client:
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": "missAV API 不可用，无法获取热榜视频",
                "results": []
            }
            
        try:
            # 重定向stdout和stderr，避免任何输出干扰JSON响应
            stdout_backup = sys.stdout
            stderr_backup = sys.stderr
            
            try:
                # 将stdout和stderr重定向到StringIO，捕获所有输出
                sys.stdout = StringIO()
                sys.stderr = StringIO()
                
                # 使用客户端获取热榜视频（网络请求）
                result = self.client.get_hot_videos(category, page)
                
            finally:
                # 恢复stdout和stderr
                sys.stdout = stdout_backup
                sys.stderr = stderr_backup
            
            # 如果网络请求成功且有结果，返回结果
            if result.get("success") and result.get("results"):
                return result
            
        except Exception as e:
            # 网络请求失败，记录错误但不返回错误
            pass
        
        # 如果网络请求也失败，最后尝试本地热榜模块作为备用
        try:
            from .hot_videos import MissAVHotVideos
            hot_videos_module = MissAVHotVideos()
            result = hot_videos_module.get_hot_videos(category, page)
            # 添加备用数据源标识
            if result.get("success"):
                result["note"] = "网络请求失败，使用本地生成的高质量模拟数据"
                result["source"] = "fallback_data"
            return result
        except Exception as fallback_error:
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": f"获取热榜失败，网络和本地模块都不可用: {str(fallback_error)}",
                "results": []
            }
    
    def download_video(self, url: str, quality: str = None, download_dir: str = None, 
                      downloader: str = None) -> dict:
        """下载视频"""
        if not self.api_available or not self.client:
            return {
                "success": False,
                "error": "missAV API 不可用，无法下载视频"
            }
            
        try:
            # 使用传入的参数或默认配置
            quality = quality or self.quality
            download_dir = download_dir or self.download_dir
            downloader = downloader or self.downloader
            
            # 确保下载目录存在
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            
            # 获取视频对象
            video = self.client.get_video(url)
            
            # 获取视频信息
            video_info = {
                "title": video.title,
                "video_code": video.video_code,
                "publish_date": video.publish_date
            }
            
            # 下载视频，使用静默回调
            success = video.download(
                quality=quality,
                downloader=downloader,
                path=download_dir,
                callback=self.silent_callback
            )
            
            if success:
                # 构建文件路径
                safe_title = self._sanitize_filename(video.title)
                file_path = Path(download_dir) / f"{safe_title}.mp4"
                
                return {
                    "success": True,
                    "video_info": video_info,
                    "file_path": str(file_path),
                    "download_dir": download_dir,
                    "quality": quality,
                    "message": f"视频下载成功: {video.title}"
                }
            else:
                return {
                    "success": False,
                    "video_info": video_info,
                    "error": "下载失败，请检查网络连接或视频URL"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"下载视频失败: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符"""
        import re
        # 移除或替换不安全的字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除前后空格
        filename = filename.strip()
        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]
        return filename