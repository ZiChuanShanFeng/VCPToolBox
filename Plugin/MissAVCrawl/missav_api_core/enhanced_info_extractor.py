#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的信息检索模块
支持提取更多视频信息，包括下载分辨率、视频时长、简介、标题等
"""

import re
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import Path


class EnhancedInfoExtractor:
    """增强的信息提取器"""
    
    def __init__(self, core=None):
        self.core = core
        self.cache_dir = Path("./cache/video_info")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 分辨率质量映射
        self.quality_map = {
            '4K': (3840, 2160),
            '1080p': (1920, 1080),
            '720p': (1280, 720),
            '480p': (854, 480),
            '360p': (640, 360),
            '240p': (426, 240)
        }
        
        # 基础URL
        self.base_url = "https://missav.ws"
    
    def extract_enhanced_video_info(self, url: str, use_cache: bool = True) -> Dict:
        """
        提取增强的视频信息
        
        Args:
            url: 视频URL
            use_cache: 是否使用缓存作为备选方案
            
        Returns:
            包含详细信息的字典
        """
        try:
            # 优先进行实时查找
            if not self.core:
                # 如果核心模块未初始化，尝试从缓存获取
                if use_cache:
                    cached_info = self._load_from_cache(url)
                    if cached_info:
                        cached_info['from_cache'] = True
                        cached_info['cache_reason'] = '核心模块未初始化'
                        return cached_info
                return {"success": False, "error": "核心模块未初始化"}
            
            # 尝试获取页面内容
            content = self.core.fetch(url)
            if not content:
                # 如果无法获取页面内容，尝试从缓存获取
                if use_cache:
                    cached_info = self._load_from_cache(url)
                    if cached_info:
                        cached_info['from_cache'] = True
                        cached_info['cache_reason'] = '无法获取页面内容'
                        return cached_info
                return {"success": False, "error": "无法获取页面内容"}
            
            # 实时提取信息
            try:
                # 提取基础信息
                basic_info = self._extract_basic_info(content, url)
                
                # 提取分辨率信息
                resolution_info = self._extract_resolution_info(content, url)
                
                # 提取视频时长
                duration_info = self._extract_duration_info(content)
                
                # 提取详细信息（演员、标签、系列等）
                detailed_info = self._extract_detailed_info(content, url)
                
                # 提取预览视频信息
                preview_info = self._extract_preview_info(content, url)
                
                # 提取封面信息
                cover_info = self._extract_cover_info(content, url)
                
                # 合并所有信息
                enhanced_info = {
                    "success": True,
                    "url": url,
                    "extraction_time": time.time(),
                    "from_cache": False,  # 明确标注这是实时获取的
                    **basic_info,
                    **resolution_info,
                    **duration_info,
                    **detailed_info,
                    **preview_info,
                    **cover_info
                }
                
                # 保存到缓存
                if use_cache:
                    self._save_to_cache(url, enhanced_info)
                
                return enhanced_info
                
            except Exception as extraction_error:
                # 如果实时提取失败，尝试从缓存获取
                if use_cache:
                    cached_info = self._load_from_cache(url)
                    if cached_info:
                        cached_info['from_cache'] = True
                        cached_info['cache_reason'] = f'实时提取失败: {str(extraction_error)}'
                        return cached_info
                
                # 如果缓存也没有，返回错误
                raise extraction_error
            
        except Exception as e:
            return {
                "success": False,
                "error": f"提取视频信息失败: {str(e)}",
                "url": url
            }
    
    def _extract_basic_info(self, content: str, url: str) -> Dict:
        """提取基础信息"""
        info = {}
        
        try:
            # 提取标题
            title_patterns = [
                r'<h1[^>]*class="[^"]*text-base[^"]*"[^>]*>(.*?)</h1>',
                r'<title>(.*?)</title>',
                r'<h1[^>]*>(.*?)</h1>',
                r'og:title"[^>]*content="([^"]*)"'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    # 清理HTML标签
                    title = re.sub(r'<[^>]+>', '', title)
                    if title and len(title) > 3:
                        info['title'] = title
                        break
            
            # 提取视频代码
            code_patterns = [
                r'<span[^>]*class="[^"]*font-medium[^"]*"[^>]*>(.*?)</span>',
                r'视频代码[：:]\s*([A-Z0-9-]+)',
                r'番号[：:]\s*([A-Z0-9-]+)',
                r'/([A-Z]{2,6}-\d{2,4})',
            ]
            
            for pattern in code_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    code = match.group(1).strip()
                    if re.match(r'^[A-Z0-9-]+$', code, re.IGNORECASE):
                        info['video_code'] = code.upper()
                        break
            
            # 从URL提取视频代码（备用方法）
            if 'video_code' not in info:
                url_code_match = re.search(r'/([A-Z]{2,6}-\d{2,4})', url, re.IGNORECASE)
                if url_code_match:
                    info['video_code'] = url_code_match.group(1).upper()
            
            # 提取发布日期
            date_patterns = [
                r'class="[^"]*font-medium[^"]*"[^>]*>(\d{4}-\d{2}-\d{2})</time>',
                r'发布日期[：:]\s*(\d{4}-\d{2}-\d{2})',
                r'上映日期[：:]\s*(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, content)
                if match:
                    info['publish_date'] = match.group(1)
                    break
            
        except Exception as e:
            info['basic_info_error'] = str(e)
        
        return info
    
    def _extract_resolution_info(self, content: str, url: str) -> Dict:
        """提取分辨率信息"""
        info = {}
        
        try:
            # 查找M3U8播放列表URL
            m3u8_patterns = [
                r"'m3u8(.*?)video",
                r'"m3u8_url":\s*"([^"]*)"',
                r'playlist\.m3u8[^"]*',
                r'master\.m3u8[^"]*'
            ]
            
            m3u8_url = None
            for pattern in m3u8_patterns:
                match = re.search(pattern, content)
                if match:
                    if pattern == r"'m3u8(.*?)video":
                        # 特殊处理MissAV的m3u8格式
                        url_parts = match.group(1).split("|")[::-1]
                        if len(url_parts) >= 8:
                            m3u8_url = f"{url_parts[1]}://{url_parts[2]}.{url_parts[3]}/{url_parts[4]}-{url_parts[5]}-{url_parts[6]}-{url_parts[7]}-{url_parts[8]}/playlist.m3u8"
                    else:
                        m3u8_url = match.group(1) if match.groups() else match.group(0)
                    break
            
            if m3u8_url:
                info['m3u8_url'] = m3u8_url
                
                # 获取可用分辨率
                resolutions = self._get_available_resolutions(m3u8_url)
                if resolutions:
                    info['available_resolutions'] = resolutions
                    info['resolution_count'] = len(resolutions)
                    
                    # 找出最高和最低分辨率
                    if resolutions:
                        sorted_res = sorted(resolutions, key=lambda x: x.get('bandwidth', 0), reverse=True)
                        info['highest_resolution'] = sorted_res[0]
                        info['lowest_resolution'] = sorted_res[-1]
            
            # 从页面内容中查找分辨率信息
            resolution_patterns = [
                r'(\d{3,4})[xX×](\d{3,4})',
                r'(\d{3,4}p)',
                r'(4K|HD|FHD|UHD)'
            ]
            
            found_resolutions = []
            for pattern in resolution_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2 and match[0].isdigit() and match[1].isdigit():
                            found_resolutions.append(f"{match[0]}x{match[1]}")
                    else:
                        found_resolutions.append(match)
            
            if found_resolutions:
                info['page_resolutions'] = list(set(found_resolutions))
            
        except Exception as e:
            info['resolution_info_error'] = str(e)
        
        return info
    
    def _get_available_resolutions(self, m3u8_url: str) -> List[Dict]:
        """获取M3U8播放列表中的可用分辨率"""
        try:
            if not self.core:
                return []
            
            # 获取主播放列表
            master_content = self.core.fetch(m3u8_url)
            if not master_content:
                return []
            
            resolutions = []
            
            # 解析EXT-X-STREAM-INF标签
            stream_pattern = r'#EXT-X-STREAM-INF:([^\n]+)\n([^\n]+)'
            matches = re.findall(stream_pattern, master_content)
            
            for info_line, url_line in matches:
                resolution_info = {}
                
                # 提取分辨率
                resolution_match = re.search(r'RESOLUTION=(\d+)x(\d+)', info_line)
                if resolution_match:
                    width, height = resolution_match.groups()
                    resolution_info['width'] = int(width)
                    resolution_info['height'] = int(height)
                    resolution_info['resolution'] = f"{width}x{height}"
                    
                    # 判断质量等级
                    for quality, (q_width, q_height) in self.quality_map.items():
                        if int(width) == q_width and int(height) == q_height:
                            resolution_info['quality'] = quality
                            break
                    else:
                        if int(height) >= 1080:
                            resolution_info['quality'] = 'HD+'
                        elif int(height) >= 720:
                            resolution_info['quality'] = 'HD'
                        else:
                            resolution_info['quality'] = 'SD'
                
                # 提取带宽（仅用于内部排序，不显示给用户）
                bandwidth_match = re.search(r'BANDWIDTH=(\d+)', info_line)
                if bandwidth_match:
                    resolution_info['bandwidth'] = int(bandwidth_match.group(1))
                    # 不再显示带宽信息给用户
                
                # 提取编码信息
                codecs_match = re.search(r'CODECS="([^"]*)"', info_line)
                if codecs_match:
                    resolution_info['codecs'] = codecs_match.group(1)
                
                # 提取帧率
                frame_rate_match = re.search(r'FRAME-RATE=([\d.]+)', info_line)
                if frame_rate_match:
                    resolution_info['frame_rate'] = float(frame_rate_match.group(1))
                
                resolution_info['url'] = url_line.strip()
                resolutions.append(resolution_info)
            
            return resolutions
            
        except Exception as e:
            return []
    
    def _extract_duration_info(self, content: str) -> Dict:
        """提取视频时长信息"""
        info = {}
        
        try:
            # 优先从og:video:duration meta标签提取（最可靠）
            og_duration_match = re.search(r'<meta[^>]*property="og:video:duration"[^>]*content="(\d+)"', content, re.IGNORECASE)
            if og_duration_match:
                total_seconds = int(og_duration_match.group(1))
                if total_seconds > 0:
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    info['duration_seconds'] = total_seconds
                    if hours > 0:
                        info['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        info['duration'] = f"{minutes}:{seconds:02d}"
                    
                    # 人性化描述
                    if hours > 0:
                        info['duration_human'] = f"{hours}小时{minutes}分钟"
                    else:
                        info['duration_human'] = f"{minutes}分钟"
                    
                    # 分类
                    if total_seconds >= 3600:
                        info['duration_category'] = 'long'  # 长片（1小时以上）
                    elif total_seconds >= 1800:
                        info['duration_category'] = 'medium'  # 中等（30分钟-1小时）
                    else:
                        info['duration_category'] = 'short'  # 短片（30分钟以下）
                    
                    return info
            
            # 如果没有找到og:video:duration，尝试其他模式
            duration_patterns = [
                # JSON中的duration字段（秒数）
                (r'"duration":\s*"?(\d+)"?', "JSON duration"),
                (r'duration["\']?\s*:\s*["\']?(\d+)["\']?', "JS duration"),
                
                # 其他meta标签
                (r'<meta[^>]*name="duration"[^>]*content="(\d+)"', "meta duration (秒数)"),
                (r'<meta[^>]*name="video:duration"[^>]*content="(\d+)"', "meta video:duration"),
                
                # 页面中的时长显示
                (r'時長[：:]\s*(\d{1,3}:\d{2})', "日文時長"),
                (r'时长[：:]\s*(\d{1,3}:\d{2})', "中文时长"),
                (r'Duration[：:]\s*(\d{1,3}:\d{2})', "英文Duration"),
                (r'長度[：:]\s*(\d{1,3}:\d{2})', "繁体長度"),
                
                # 带小时的格式
                (r'時長[：:]\s*(\d{1,2}:\d{2}:\d{2})', "日文時長(带小时)"),
                (r'时长[：:]\s*(\d{1,2}:\d{2}:\d{2})', "中文时长(带小时)"),
                (r'Duration[：:]\s*(\d{1,2}:\d{2}:\d{2})', "英文Duration(带小时)"),
                
                # 从视频信息区域提取
                (r'<div[^>]*class="[^"]*duration[^"]*"[^>]*>.*?(\d{1,3}:\d{2}).*?</div>', "duration class区域"),
                (r'<span[^>]*class="[^"]*time[^"]*"[^>]*>(\d{1,3}:\d{2})</span>', "time class区域"),
                
                # 从meta标签提取时间格式
                (r'<meta[^>]*name="duration"[^>]*content="(\d{1,3}:\d{2})"', "meta duration (时间)"),
                
                # 从script标签中的变量提取
                (r'var\s+duration\s*=\s*["\'](\d{1,3}:\d{2})["\']', "JS变量duration"),
                (r'duration\s*=\s*["\'](\d{1,3}:\d{2})["\']', "JS赋值duration"),
            ]
            
            # 尝试其他模式
            duration_found = False
            
            for pattern, description in duration_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    duration_str = match.strip()
                    
                    # 跳过明显错误的时长
                    if not duration_str or duration_str in ['0', '00:00', '0:00']:
                        continue
                    
                    # 解析时长
                    if duration_str.isdigit():
                        # 纯数字，认为是秒数
                        total_seconds = int(duration_str)
                        if total_seconds > 0:  # 确保不是0
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            
                            info['duration_seconds'] = total_seconds
                            if hours > 0:
                                info['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                            else:
                                info['duration'] = f"{minutes}:{seconds:02d}"
                            
                            # 人性化描述
                            if hours > 0:
                                info['duration_human'] = f"{hours}小时{minutes}分钟"
                            else:
                                info['duration_human'] = f"{minutes}分钟"
                            
                            # 分类
                            if total_seconds >= 3600:
                                info['duration_category'] = 'long'
                            elif total_seconds >= 1800:
                                info['duration_category'] = 'medium'
                            else:
                                info['duration_category'] = 'short'
                            
                            duration_found = True
                            break
                    elif ':' in duration_str:
                        # 时间格式
                        try:
                            time_parts = duration_str.split(':')
                            if len(time_parts) == 2:
                                # MM:SS 格式
                                minutes, seconds = map(int, time_parts)
                                if minutes > 0 or seconds > 0:  # 确保不是00:00
                                    total_seconds = minutes * 60 + seconds
                                    info['duration_seconds'] = total_seconds
                                    info['duration'] = f"{minutes}:{seconds:02d}"
                                    info['duration_human'] = f"{minutes}分钟"
                                    info['duration_category'] = 'short' if total_seconds < 1800 else 'medium'
                                    duration_found = True
                                    break
                            elif len(time_parts) == 3:
                                # HH:MM:SS 格式
                                hours, minutes, seconds = map(int, time_parts)
                                if hours > 0 or minutes > 0 or seconds > 0:  # 确保不是00:00:00
                                    total_seconds = hours * 3600 + minutes * 60 + seconds
                                    info['duration_seconds'] = total_seconds
                                    info['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                                    if hours > 0:
                                        info['duration_human'] = f"{hours}小时{minutes}分钟"
                                    else:
                                        info['duration_human'] = f"{minutes}分钟"
                                    info['duration_category'] = 'long' if total_seconds >= 3600 else ('medium' if total_seconds >= 1800 else 'short')
                                    duration_found = True
                                    break
                        except ValueError:
                            continue
                
                if duration_found:
                    break
            
        except Exception as e:
            info['duration_info_error'] = str(e)
        
        return info
    
    def _extract_detailed_info(self, content: str, url: str) -> Dict:
        """提取详细信息：演员、标签、系列、发行商等"""
        info = {}
        
        try:
            # 提取简介/描述
            description = self._extract_description(content)
            if description:
                info['description'] = description
                info['description_length'] = len(description)
                # 简介摘要（前200字符）
                if len(description) > 200:
                    info['description_summary'] = description[:200] + "..."
                else:
                    info['description_summary'] = description
            
            # 提取发行日期（更精确）
            release_date = self._extract_release_date(content)
            if release_date:
                info['release_date'] = release_date
            
            # 提取番号（视频代码的另一种表达）
            video_code = self._extract_video_code(content, url)
            if video_code:
                info['video_code'] = video_code
                info['番號'] = video_code  # 添加中文字段
            
            # 提取演员信息（带链接）
            actresses_info = self._extract_actresses_with_links(content)
            if actresses_info:
                info['actresses'] = [actress['name'] for actress in actresses_info]
                info['actresses_with_links'] = actresses_info
                info['actress_count'] = len(actresses_info)
                info['女優'] = actresses_info  # 添加中文字段
            
            # 提取类型/标签（带链接）
            types_info = self._extract_types_with_links(content)
            if types_info:
                info['types'] = [type_item['name'] for type_item in types_info]
                info['types_with_links'] = types_info
                info['type_count'] = len(types_info)
                info['類型'] = types_info  # 添加中文字段
            
            # 提取系列信息（带链接）
            series_info = self._extract_series_with_links(content)
            if series_info:
                info['series'] = series_info['name']
                info['series_with_link'] = series_info
                info['系列'] = series_info  # 添加中文字段
            
            # 提取发行商信息（带链接）
            publisher_info = self._extract_publisher_with_links(content)
            if publisher_info:
                info['publisher'] = publisher_info['name']
                info['publisher_with_link'] = publisher_info
                info['發行商'] = publisher_info  # 添加中文字段
            
            # 提取标签信息（带链接）
            tags_info = self._extract_tags_with_links(content)
            if tags_info:
                info['tags'] = [tag['name'] for tag in tags_info]
                info['tags_with_links'] = tags_info
                info['tag_count'] = len(tags_info)
                info['標籤'] = tags_info  # 添加中文字段
            
        except Exception as e:
            info['detailed_info_error'] = str(e)
        
        return info
    
    def _extract_description(self, content: str) -> str:
        """提取视频描述/简介"""
        description_patterns = [
            # Meta标签中的描述
            r'<meta[^>]*name="description"[^>]*content="([^"]*)"',
            r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"',
            
            # 页面中的描述区域
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>',
            r'<div[^>]*class="[^"]*summary[^"]*"[^>]*>(.*?)</div>',
            
            # 中文标签
            r'简介[：:]\s*([^<\n]+)',
            r'介绍[：:]\s*([^<\n]+)',
            r'內容[：:]\s*([^<\n]+)',
            
            # 英文标签
            r'Description[：:]\s*([^<\n]+)',
            r'Summary[：:]\s*([^<\n]+)',
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                # 清理HTML标签
                description = re.sub(r'<[^>]+>', '', description)
                # 清理多余空白
                description = ' '.join(description.split())
                # 解码HTML实体
                description = description.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                
                if description and len(description) > 10:
                    return description
        
        return ""
    
    def _extract_release_date(self, content: str) -> str:
        """提取发行日期"""
        date_patterns = [
            # 发行日期相关
            r'發行日期[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'发行日期[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'Release Date[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'上映日期[：:]\s*(\d{4}-\d{2}-\d{2})',
            
            # 从time标签提取
            r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})"',
            r'<time[^>]*>(\d{4}-\d{2}-\d{2})</time>',
            
            # 从meta标签提取
            r'<meta[^>]*name="release_date"[^>]*content="(\d{4}-\d{2}-\d{2})"',
            
            # 通用日期格式
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_video_code(self, content: str, url: str) -> str:
        """提取视频代码/番号"""
        code_patterns = [
            # 从页面内容提取
            r'番號[：:]\s*([A-Z0-9-]+)',
            r'品番[：:]\s*([A-Z0-9-]+)',
            r'Code[：:]\s*([A-Z0-9-]+)',
            r'<span[^>]*class="[^"]*code[^"]*"[^>]*>([A-Z0-9-]+)</span>',
            
            # 从URL提取
            r'/([A-Z]{2,6}-\d{2,4})',
            r'/dm\d+/([a-zA-Z]+-\d+)',
        ]
        
        for pattern in code_patterns:
            if pattern.startswith('/'):
                # URL模式
                match = re.search(pattern, url, re.IGNORECASE)
            else:
                # 内容模式
                match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                code = match.group(1).strip().upper()
                if re.match(r'^[A-Z0-9-]+$', code):
                    return code
        
        return ""
    
    def _extract_actresses_with_links(self, content: str) -> List[Dict]:
        """提取演员信息（包含链接）"""
        actresses = []
        
        # 演员链接模式
        actress_patterns = [
            r'<a[^>]*href="([^"]*(?:actress|女優|performer)[^"]*)"[^>]*>([^<]+)</a>',
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*actress[^"]*"[^>]*>([^<]+)</a>',
            r'href="(/[^"]*actress[^"]*)"[^>]*>([^<]+)</a>',
        ]
        
        for pattern in actress_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                link, name = match
                name = name.strip()
                if name and len(name) > 1:
                    # 构建完整链接
                    if link.startswith('/'):
                        link = self.base_url + link
                    elif not link.startswith('http'):
                        link = self.base_url + '/' + link
                    
                    actress_info = {
                        'name': name,
                        'link': link
                    }
                    
                    # 避免重复
                    if not any(a['name'] == name for a in actresses):
                        actresses.append(actress_info)
        
        # 如果没有找到链接，尝试提取纯文本演员名
        if not actresses:
            text_patterns = [
                r'女優[：:]\s*([^<\n]+)',
                r'演员[：:]\s*([^<\n]+)',
                r'Actress[：:]\s*([^<\n]+)',
                r'出演[：:]\s*([^<\n]+)',
            ]
            
            for pattern in text_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    names_text = match.group(1).strip()
                    # 分割多个演员名
                    names = re.split(r'[,，、]', names_text)
                    for name in names:
                        name = name.strip()
                        if name and len(name) > 1:
                            actresses.append({
                                'name': name,
                                'link': ''
                            })
                    break
        
        return actresses
    
    def _extract_types_with_links(self, content: str) -> List[Dict]:
        """提取类型/标签信息（包含链接）"""
        types = []
        
        # 类型链接模式
        type_patterns = [
            r'<a[^>]*href="([^"]*(?:genre|tag|category|類型)[^"]*)"[^>]*>([^<]+)</a>',
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*(?:genre|tag|category)[^"]*"[^>]*>([^<]+)</a>',
            r'href="(/[^"]*(?:genre|tag)[^"]*)"[^>]*>([^<]+)</a>',
        ]
        
        for pattern in type_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                link, name = match
                name = name.strip()
                if name and len(name) > 1:
                    # 构建完整链接
                    if link.startswith('/'):
                        link = self.base_url + link
                    elif not link.startswith('http'):
                        link = self.base_url + '/' + link
                    
                    type_info = {
                        'name': name,
                        'link': link
                    }
                    
                    # 避免重复
                    if not any(t['name'] == name for t in types):
                        types.append(type_info)
        
        return types
    
    def _extract_series_with_links(self, content: str) -> Dict:
        """提取系列信息（包含链接）"""
        series_patterns = [
            r'<a[^>]*href="([^"]*(?:series|系列)[^"]*)"[^>]*>([^<]+)</a>',
            r'系列[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
            r'Series[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
        ]
        
        for pattern in series_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                link, name = match.groups()
                name = name.strip()
                if name and len(name) > 1:
                    # 构建完整链接
                    if link.startswith('/'):
                        link = self.base_url + link
                    elif not link.startswith('http'):
                        link = self.base_url + '/' + link
                    
                    return {
                        'name': name,
                        'link': link
                    }
        
        # 如果没有找到链接，尝试提取纯文本
        text_patterns = [
            r'系列[：:]\s*([^<\n]+)',
            r'Series[：:]\s*([^<\n]+)',
        ]
        
        for pattern in text_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:
                    return {
                        'name': name,
                        'link': ''
                    }
        
        return {}
    
    def _extract_publisher_with_links(self, content: str) -> Dict:
        """提取发行商信息（包含链接）"""
        publisher_patterns = [
            r'<a[^>]*href="([^"]*(?:studio|publisher|maker|發行商)[^"]*)"[^>]*>([^<]+)</a>',
            r'發行商[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
            r'Studio[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
            r'Maker[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
        ]
        
        for pattern in publisher_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                link, name = match.groups()
                name = name.strip()
                if name and len(name) > 1:
                    # 构建完整链接
                    if link.startswith('/'):
                        link = self.base_url + link
                    elif not link.startswith('http'):
                        link = self.base_url + '/' + link
                    
                    return {
                        'name': name,
                        'link': link
                    }
        
        # 如果没有找到链接，尝试提取纯文本
        text_patterns = [
            r'發行商[：:]\s*([^<\n]+)',
            r'发行商[：:]\s*([^<\n]+)',
            r'Studio[：:]\s*([^<\n]+)',
            r'Maker[：:]\s*([^<\n]+)',
        ]
        
        for pattern in text_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:
                    return {
                        'name': name,
                        'link': ''
                    }
        
        return {}
    
    def _extract_tags_with_links(self, content: str) -> List[Dict]:
        """提取标签信息（包含链接）"""
        tags = []
        
        # 标签链接模式
        tag_patterns = [
            r'<a[^>]*href="([^"]*(?:tag|label|標籤)[^"]*)"[^>]*>([^<]+)</a>',
            r'標籤[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
            r'Tags[：:]\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>',
        ]
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                link, name = match
                name = name.strip()
                if name and len(name) > 1:
                    # 构建完整链接
                    if link.startswith('/'):
                        link = self.base_url + link
                    elif not link.startswith('http'):
                        link = self.base_url + '/' + link
                    
                    tag_info = {
                        'name': name,
                        'link': link
                    }
                    
                    # 避免重复
                    if not any(t['name'] == name for t in tags):
                        tags.append(tag_info)
        
        return tags
    
    def _extract_preview_info(self, content: str, url: str) -> Dict:
        """提取预览视频信息"""
        info = {}
        
        try:
            # 从URL提取DVD ID
            dvd_id = self._extract_dvd_id_from_url(url)
            
            if dvd_id:
                # 基于发现的cdnUrl函数构造预览视频URL
                # cdnUrl(path) { return `https://fourhoi.com${path}` }
                # 预览视频模式: cdnUrl(`/${item.dvd_id}/preview.mp4`)
                preview_url = f"https://fourhoi.com/{dvd_id}/preview.mp4"
                
                # 验证预览视频URL是否可访问
                if self._verify_preview_url(preview_url):
                    info['preview_videos'] = [preview_url]
                    info['preview_count'] = 1
                    info['has_preview'] = True
                    info['main_preview'] = preview_url
                else:
                    info['has_preview'] = False
                    info['preview_count'] = 0
            else:
                info['has_preview'] = False
                info['preview_count'] = 0
                info['preview_extraction_error'] = 'Unable to extract DVD ID from URL'
            
            # 查找预览图片（保留原有逻辑）
            preview_image_patterns = [
                r'data-src="([^"]*preview[^"]*)"',
                r'src="([^"]*preview[^"]*)"',
                r'"preview_image":\s*"([^"]*)"',
            ]
            
            preview_images = []
            for pattern in preview_image_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match and match not in preview_images:
                        if match.startswith('http'):
                            preview_images.append(match)
                        elif match.startswith('/'):
                            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                            preview_images.append(urljoin(base_url, match))
            
            if preview_images:
                info['preview_images'] = preview_images
                info['preview_image_count'] = len(preview_images)
            
        except Exception as e:
            info['preview_info_error'] = str(e)
            info['has_preview'] = False
            info['preview_count'] = 0
        
        return info
    
    def _extract_dvd_id_from_url(self, url: str) -> Optional[str]:
        """从URL提取DVD ID"""
        try:
            # 从URL路径中提取最后一部分作为DVD ID
            # 例如: https://missav.ws/dm44/jul-875 -> jul-875
            path_parts = url.rstrip('/').split('/')
            if path_parts:
                dvd_id = path_parts[-1]
                # 验证DVD ID格式（通常包含字母和数字，可能有连字符）
                if re.match(r'^[a-zA-Z0-9\-]+$', dvd_id) and len(dvd_id) > 2:
                    return dvd_id
        except Exception:
            pass
        return None
    
    def _verify_preview_url(self, preview_url: str) -> bool:
        """验证预览视频URL是否可访问"""
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://missav.ws/',
                'Accept': 'video/mp4,video/*,*/*;q=0.9',
            }
            
            response = requests.head(preview_url, headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _extract_cover_info(self, content: str, url: str) -> Dict:
        """提取封面信息"""
        info = {}
        
        try:
            # 查找封面图片
            cover_patterns = [
                r'og:image"[^>]*content="([^"]*)"',
                r'"thumbnail":\s*"([^"]*)"',
                r'<img[^>]*class="[^"]*cover[^"]*"[^>]*src="([^"]*)"',
                r'cover-n\.jpg',
                r'poster[^"]*"([^"]*)"',
            ]
            
            cover_urls = []
            for pattern in cover_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match:
                        # 构建完整URL
                        if match.startswith('http'):
                            cover_urls.append(match)
                        elif match.startswith('/'):
                            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                            cover_urls.append(urljoin(base_url, match))
            
            if cover_urls:
                info['cover_images'] = list(set(cover_urls))
                info['main_cover'] = cover_urls[0]
                info['cover_count'] = len(cover_urls)
            
            # 查找高清封面
            hd_cover_patterns = [
                r'cover-n\.jpg',
                r'cover-hd\.jpg',
                r'poster-hd\.jpg',
            ]
            
            for pattern in hd_cover_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    info['has_hd_cover'] = True
                    break
            else:
                info['has_hd_cover'] = False
            
        except Exception as e:
            info['cover_info_error'] = str(e)
        
        return info
    
    def _load_from_cache(self, url: str) -> Optional[Dict]:
        """从缓存加载信息"""
        try:
            # 生成缓存文件名
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_file = self.cache_dir / f"{url_hash}.json"
            
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # 检查缓存是否过期（24小时）
                if time.time() - cached_data.get('extraction_time', 0) < 86400:
                    cached_data['from_cache'] = True
                    return cached_data
            
        except Exception:
            pass
        
        return None
    
    def _save_to_cache(self, url: str, info: Dict) -> None:
        """保存信息到缓存"""
        try:
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_file = self.cache_dir / f"{url_hash}.json"
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
                
        except Exception:
            pass
    
    def format_info_response(self, info: Dict) -> str:
        """格式化信息响应为文本"""
        if not info.get("success"):
            return f"获取视频信息失败: {info.get('error', '未知错误')}"
        
        response_text = "### MissAV 增强视频信息 ###\n\n"
        
        # 基础信息
        if info.get('title'):
            response_text += f"**標題**: {info['title']}\n"
        
        if info.get('video_code'):
            response_text += f"**番號**: {info['video_code']}\n"
        
        if info.get('release_date'):
            response_text += f"**發行日期**: {info['release_date']}\n"
        elif info.get('publish_date'):
            response_text += f"**發行日期**: {info['publish_date']}\n"
        
        # 时长信息
        if info.get('duration') and info.get('duration') != '00:00:00':
            response_text += f"**時長**: {info['duration']}"
            if info.get('duration_human'):
                response_text += f" ({info['duration_human']})"
            response_text += "\n"
        
        # 演员信息（带链接）
        if info.get('actresses_with_links'):
            response_text += f"\n**女優**: "
            actress_list = []
            for actress in info['actresses_with_links']:
                if actress.get('link'):
                    actress_list.append(f"[{actress['name']}]({actress['link']})")
                else:
                    actress_list.append(actress['name'])
            response_text += ', '.join(actress_list) + "\n"
        elif info.get('actresses'):
            response_text += f"\n**女優**: {', '.join(info['actresses'])}\n"
        
        # 类型信息（带链接）
        if info.get('types_with_links'):
            response_text += f"**類型**: "
            type_list = []
            for type_item in info['types_with_links']:
                if type_item.get('link'):
                    type_list.append(f"[{type_item['name']}]({type_item['link']})")
                else:
                    type_list.append(type_item['name'])
            response_text += ', '.join(type_list) + "\n"
        elif info.get('types'):
            response_text += f"**類型**: {', '.join(info['types'])}\n"
        
        # 系列信息（带链接）
        if info.get('series_with_link'):
            series = info['series_with_link']
            if series.get('link'):
                response_text += f"**系列**: [{series['name']}]({series['link']})\n"
            else:
                response_text += f"**系列**: {series['name']}\n"
        elif info.get('series'):
            response_text += f"**系列**: {info['series']}\n"
        
        # 发行商信息（带链接）
        if info.get('publisher_with_link'):
            publisher = info['publisher_with_link']
            if publisher.get('link'):
                response_text += f"**發行商**: [{publisher['name']}]({publisher['link']})\n"
            else:
                response_text += f"**發行商**: {publisher['name']}\n"
        elif info.get('publisher'):
            response_text += f"**發行商**: {info['publisher']}\n"
        
        # 标签信息（带链接）
        if info.get('tags_with_links'):
            response_text += f"**標籤**: "
            tag_list = []
            for tag in info['tags_with_links']:
                if tag.get('link'):
                    tag_list.append(f"[{tag['name']}]({tag['link']})")
                else:
                    tag_list.append(tag['name'])
            response_text += ', '.join(tag_list) + "\n"
        elif info.get('tags'):
            response_text += f"**標籤**: {', '.join(info['tags'])}\n"
        
        # 分辨率信息（不显示带宽）
        if info.get('available_resolutions'):
            response_text += f"\n**可用分辨率** ({info.get('resolution_count', 0)}个):\n"
            for i, res in enumerate(info['available_resolutions'][:5], 1):  # 最多显示5个
                quality = res.get('quality', '未知')
                resolution = res.get('resolution', '未知')
                response_text += f"  {i}. {quality} ({resolution})\n"
            
            if len(info['available_resolutions']) > 5:
                response_text += f"  ... 还有 {len(info['available_resolutions']) - 5} 个分辨率\n"
        
        # 简介信息
        if info.get('description_summary'):
            response_text += f"\n**簡介**: {info['description_summary']}\n"
        
        # 封面和预览
        if info.get('main_cover'):
            response_text += f"\n**封面圖片**: {info['main_cover']}\n"
        
        if info.get('has_preview'):
            response_text += f"**預覽視頻**: 可用 ({info.get('preview_count', 0)}个)\n"
            if info.get('preview_videos'):
                response_text += f"  主預覽: {info['preview_videos'][0]}\n"
        
        # 技术信息
        if info.get('m3u8_url'):
            response_text += f"\n**M3U8播放列表**: {info['m3u8_url']}\n"
        
        response_text += f"\n**原始URL**: {info['url']}\n"
        
        # 缓存信息
        if info.get('from_cache'):
            cache_reason = info.get('cache_reason', '使用缓存数据')
            response_text += f"\n💾 **信息来源**: 缓存数据 ({cache_reason})\n"
        else:
            response_text += f"\n🔄 **信息来源**: 实时获取\n"
        
        return response_text


def test_enhanced_info_extractor():
    """测试增强信息提取器"""
    print("🔍 测试增强信息提取器")
    print("=" * 50)
    
    # 这里需要一个实际的core实例来测试
    # extractor = EnhancedInfoExtractor(core=some_core)
    # result = extractor.extract_enhanced_video_info("https://missav.ws/some-video")
    # print(extractor.format_info_response(result))
    
    print("✅ 增强信息提取器模块已创建")


if __name__ == "__main__":
    test_enhanced_info_extractor()