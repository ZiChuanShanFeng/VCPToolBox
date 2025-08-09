#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本的BaseCore - 替代原有的base_api模块
"""

import time
import random
import httpx
import requests
from typing import Optional, Dict, Any
from pathlib import Path

class Config:
    """配置类"""
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.missav.ws',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        }

class BaseCore:
    """修复版本的BaseCore - 解决403反爬虫问题"""
    
    def __init__(self):
        self.config = Config()
        self.session = None
        self.last_request_time = 0
        self.min_delay = 1  # 最小延迟1秒
        self.max_delay = 3  # 最大延迟3秒
        
        # 多个User-Agent轮换
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # 多个Referer
        self.referers = [
            'https://www.google.com/',
            'https://missav.ws/',
            'https://www.missav.ws/',
            'https://missav.com/'
        ]
    
    def initialize_session(self):
        """初始化会话"""
        if self.session is None:
            self.session = httpx.Client(
                timeout=30,
                follow_redirects=True,
                verify=True
            )
    
    def get_enhanced_headers(self) -> Dict[str, str]:
        """获取增强的请求头"""
        headers = self.config.headers.copy()
        
        # 随机化User-Agent和Referer
        headers['User-Agent'] = random.choice(self.user_agents)
        headers['Referer'] = random.choice(self.referers)
        
        # 添加更多反爬虫头部
        headers.update({
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return headers
    
    def wait_between_requests(self):
        """请求间延迟"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay - elapsed, self.max_delay - elapsed)
            if delay > 0:
                time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def fetch(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        修复版本的fetch方法 - 解决403问题
        """
        if self.session is None:
            self.initialize_session()
        
        for attempt in range(max_retries):
            try:
                # 请求间延迟
                self.wait_between_requests()
                
                # 获取增强的请求头
                headers = self.get_enhanced_headers()
                
                # 更新session的headers
                self.session.headers.update(headers)
                
                # 发送请求
                response = self.session.get(url)
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 403:
                    # 403错误，增加延迟后重试
                    if attempt < max_retries - 1:
                        delay = random.uniform(2, 5)
                        time.sleep(delay)
                    continue
                else:
                    # 其他HTTP错误
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(1, 3))
                    continue
                    
            except Exception as e:
                # 网络异常，重试
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                continue
        
        # 所有重试都失败，尝试使用requests作为备用
        return self._fallback_fetch(url)
    
    def _fallback_fetch(self, url: str) -> Optional[str]:
        """备用fetch方法 - 使用requests"""
        try:
            headers = self.get_enhanced_headers()
            
            # 使用requests作为备用
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response.text
                
        except Exception:
            pass
        
        return None
    
    def get_segments(self, quality: str, m3u8_url_master: str) -> list:
        """获取HLS分段列表"""
        try:
            # 获取主播放列表
            master_content = self.fetch(m3u8_url_master)
            if not master_content:
                return []
            
            # 解析质量选项
            import re
            # 匹配 EXT-X-STREAM-INF 行和对应的URL行
            stream_info_pattern = r'#EXT-X-STREAM-INF:([^\n]+)\n([^\n]+)'
            matches = re.findall(stream_info_pattern, master_content)
            
            if not matches:
                return []
            
            # 解析每个流的信息
            streams = []
            for info_line, url_line in matches:
                # 提取分辨率和带宽信息
                resolution_match = re.search(r'RESOLUTION=(\d+)x(\d+)', info_line)
                bandwidth_match = re.search(r'BANDWIDTH=(\d+)', info_line)
                
                width = int(resolution_match.group(1)) if resolution_match else 0
                height = int(resolution_match.group(2)) if resolution_match else 0
                bandwidth = int(bandwidth_match.group(1)) if bandwidth_match else 0
                
                streams.append({
                    'url': url_line.strip(),
                    'width': width,
                    'height': height,
                    'bandwidth': bandwidth,
                    'resolution': f"{width}x{height}" if width and height else "unknown"
                })
            
            # 按带宽排序（带宽越高质量越好）
            streams.sort(key=lambda x: x['bandwidth'], reverse=True)
            
            # 选择质量
            if quality == "worst":
                selected_stream = streams[-1]  # 最低质量（最低带宽）
            elif quality == "best":
                selected_stream = streams[0]   # 最高质量（最高带宽）
            elif quality.endswith('p'):
                # 尝试匹配特定分辨率，如 "720p", "1080p"
                target_height = int(quality[:-1])
                # 找到最接近的分辨率
                best_match = min(streams, key=lambda x: abs(x['height'] - target_height))
                selected_stream = best_match
            else:
                selected_stream = streams[0]   # 默认最高质量
            
            selected_url = selected_stream['url']
            
            # 记录选择的质量信息
            print(f"🎯 选择质量: {selected_stream['resolution']} (带宽: {selected_stream['bandwidth']})")
            print(f"📊 可用质量: {[s['resolution'] for s in streams]}")
            
            # 构建完整URL
            if not selected_url.startswith('http'):
                base_url = '/'.join(m3u8_url_master.split('/')[:-1])
                selected_url = f"{base_url}/{selected_url}"
            
            # 获取分段播放列表
            segments_content = self.fetch(selected_url)
            if not segments_content:
                return []
            
            # 解析分段
            segment_lines = re.findall(r'^(?!#)(.+)$', segments_content, re.MULTILINE)
            
            # 构建完整的分段URL
            segments = []
            base_url = '/'.join(selected_url.split('/')[:-1])
            
            for segment in segment_lines:
                if segment.strip():
                    if segment.startswith('http'):
                        segments.append(segment)
                    else:
                        segments.append(f"{base_url}/{segment}")
            
            return segments
            
        except Exception as e:
            print(f"❌ 获取分段失败: {str(e)}")
            return []
    
    def truncate(self, text, max_length=100):
        """截断文本到指定长度"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def strip_title(self, title):
        """清理标题中的非法字符"""
        import re
        # 移除或替换文件名中的非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        cleaned = re.sub(illegal_chars, '_', title)
        # 移除多余的空格
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    def download(self, video, quality, path, callback, downloader, remux=False, callback_remux=None):
        """下载视频的方法"""
        try:
            # 获取分段
            segments = video.get_segments(quality)
            if not segments:
                print("获取视频分段失败")
                return False
            
            print(f"获取到 {len(segments)} 个视频分段")
            
            # 处理路径 - path可能是目录或文件路径
            from pathlib import Path
            path_obj = Path(path)
            
            if path_obj.suffix == '.mp4':
                # 如果path已经包含文件名，直接使用
                output_file = path_obj
                output_dir = path_obj.parent
            else:
                # 如果path是目录，生成文件名
                output_dir = path_obj
                clean_title = self.strip_title(video.title)
                truncated_title = self.truncate(clean_title, 50)
                filename = f"{truncated_title}.mp4"
                output_file = output_dir / filename
            
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"准备下载到: {output_file}")
            
            # 下载分段
            import requests
            import tempfile
            import shutil
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                downloaded_segments = 0
                failed_segments = 0
                
                # 下载所有分段
                for i, segment_url in enumerate(segments):
                    if callback:
                        callback(i + 1, len(segments))
                    
                    try:
                        response = self.session.get(segment_url, timeout=30)
                        response.raise_for_status()
                        
                        segment_file = temp_path / f"segment_{i:04d}.ts"
                        with open(segment_file, 'wb') as f:
                            f.write(response.content)
                        
                        # 检查分段文件大小
                        if segment_file.stat().st_size > 0:
                            downloaded_segments += 1
                        else:
                            failed_segments += 1
                            print(f"分段 {i} 下载为空文件")
                            
                    except Exception as e:
                        failed_segments += 1
                        print(f"下载分段 {i} 失败: {e}")
                        continue
                
                print(f"下载完成: 成功 {downloaded_segments} 个，失败 {failed_segments} 个")
                
                # 从环境变量获取最小成功率配置
                import os
                min_success_rate = float(os.getenv('MISSAV_MIN_SUCCESS_RATE', '0.8'))
                
                # 检查下载成功率
                success_rate = downloaded_segments / len(segments) if len(segments) > 0 else 0
                if success_rate < min_success_rate:  # 如果成功率低于配置值，认为下载失败
                    print(f"下载成功率过低: {success_rate:.2%} < {min_success_rate:.2%}")
                    return False
                
                # 合并分段
                segments_files = sorted(temp_path.glob("segment_*.ts"))
                if segments_files:
                    total_size = 0
                    with open(output_file, 'wb') as outfile:
                        for segment_file in segments_files:
                            if segment_file.stat().st_size > 0:  # 只合并非空文件
                                with open(segment_file, 'rb') as infile:
                                    data = infile.read()
                                    outfile.write(data)
                                    total_size += len(data)
                    
                    print(f"文件合并完成，总大小: {total_size / (1024*1024):.2f} MB")
                    
                    # 检查最终文件大小
                    if output_file.exists() and output_file.stat().st_size > 1024 * 1024:  # 至少1MB
                        return True
                    else:
                        print(f"最终文件过小或不存在: {output_file.stat().st_size if output_file.exists() else 0} bytes")
                        return False
                else:
                    print("没有找到任何下载的分段文件")
                    return False
                    
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
            self.session = None