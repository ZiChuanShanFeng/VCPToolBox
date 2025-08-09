#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览视频下载模块
支持下载视频的预览小视频（鼠标悬停时显示的内容速览视频）
"""

import os
import re
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse


class PreviewDownloader:
    """预览视频下载器"""
    
    def __init__(self, core=None, cache_dir: str = "./cache/previews"):
        self.core = core
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载配置
        self.download_timeout = 30
        self.max_retries = 3
        self.chunk_size = 8192
        
        # 支持的预览视频格式
        self.supported_formats = ['.mp4', '.webm', '.mov', '.avi']
        
        # 预览视频的常见URL模式
        self.preview_patterns = [
            r'"preview":\s*"([^"]*\.(?:mp4|webm|mov))"',
            r'"hover_video":\s*"([^"]*\.(?:mp4|webm|mov))"',
            r'"preview_video":\s*"([^"]*\.(?:mp4|webm|mov))"',
            r'data-preview="([^"]*\.(?:mp4|webm|mov))"',
            r'data-hover="([^"]*\.(?:mp4|webm|mov))"',
            r'preview[_-]?video[^"]*"([^"]*\.(?:mp4|webm|mov))"',
            r'hover[_-]?video[^"]*"([^"]*\.(?:mp4|webm|mov))"',
            r'onmouseover[^"]*"([^"]*\.(?:mp4|webm|mov))"',
        ]
    
    def extract_preview_urls(self, url: str, content: Optional[str] = None) -> Dict:
        """
        从视频页面提取预览视频URL
        
        Args:
            url: 视频页面URL
            content: 页面内容（可选，如果不提供会自动获取）
            
        Returns:
            包含预览视频URL的字典
        """
        try:
            # 获取页面内容
            if not content:
                if not self.core:
                    return {"success": False, "error": "核心模块未初始化且未提供页面内容"}
                
                content = self.core.fetch(url)
                if not content:
                    return {"success": False, "error": "无法获取页面内容"}
            
            preview_urls = []
            
            # 使用多种模式提取预览视频URL
            for pattern in self.preview_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match and match not in preview_urls:
                        # 构建完整URL
                        if match.startswith('http'):
                            preview_urls.append(match)
                        elif match.startswith('/'):
                            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                            preview_urls.append(urljoin(base_url, match))
                        else:
                            preview_urls.append(urljoin(url, match))
            
            # 查找JavaScript中的预览视频配置
            js_preview_urls = self._extract_js_preview_urls(content, url)
            preview_urls.extend(js_preview_urls)
            
            # 查找CSS中的预览视频
            css_preview_urls = self._extract_css_preview_urls(content, url)
            preview_urls.extend(css_preview_urls)
            
            # 去重
            preview_urls = list(set(preview_urls))
            
            # 验证URL有效性
            valid_urls = []
            for preview_url in preview_urls:
                if self._is_valid_preview_url(preview_url):
                    valid_urls.append(preview_url)
            
            return {
                "success": True,
                "url": url,
                "preview_urls": valid_urls,
                "preview_count": len(valid_urls),
                "extraction_time": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": f"提取预览视频URL失败: {str(e)}"
            }
    
    def _extract_js_preview_urls(self, content: str, base_url: str) -> List[str]:
        """从JavaScript代码中提取预览视频URL"""
        urls = []
        
        try:
            # 查找JavaScript变量中的预览视频配置
            js_patterns = [
                r'var\s+preview\s*=\s*["\']([^"\']*\.(?:mp4|webm|mov))["\']',
                r'preview\s*:\s*["\']([^"\']*\.(?:mp4|webm|mov))["\']',
                r'hoverVideo\s*:\s*["\']([^"\']*\.(?:mp4|webm|mov))["\']',
                r'previewSrc\s*:\s*["\']([^"\']*\.(?:mp4|webm|mov))["\']',
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.startswith('http'):
                        urls.append(match)
                    elif match.startswith('/'):
                        urls.append(urljoin(base_url, match))
            
            # 查找JSON配置中的预览视频
            json_patterns = [
                r'\{[^}]*"preview":\s*"([^"]*\.(?:mp4|webm|mov))"[^}]*\}',
                r'\{[^}]*"hover_video":\s*"([^"]*\.(?:mp4|webm|mov))"[^}]*\}',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.startswith('http'):
                        urls.append(match)
                    elif match.startswith('/'):
                        urls.append(urljoin(base_url, match))
            
        except Exception:
            pass
        
        return urls
    
    def _extract_css_preview_urls(self, content: str, base_url: str) -> List[str]:
        """从CSS样式中提取预览视频URL"""
        urls = []
        
        try:
            # 查找CSS中的background-image或content属性中的视频URL
            css_patterns = [
                r'background-image:\s*url\(["\']?([^"\']*\.(?:mp4|webm|mov))["\']?\)',
                r'content:\s*url\(["\']?([^"\']*\.(?:mp4|webm|mov))["\']?\)',
            ]
            
            for pattern in css_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.startswith('http'):
                        urls.append(match)
                    elif match.startswith('/'):
                        urls.append(urljoin(base_url, match))
            
        except Exception:
            pass
        
        return urls
    
    def _is_valid_preview_url(self, url: str) -> bool:
        """验证预览视频URL是否有效"""
        try:
            # 检查URL格式
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # 检查文件扩展名
            path = parsed.path.lower()
            if not any(path.endswith(ext) for ext in self.supported_formats):
                return False
            
            # 检查URL是否包含预览相关关键词
            preview_keywords = ['preview', 'hover', 'thumb', 'sample']
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in preview_keywords):
                return True
            
            # 检查文件名是否符合预览视频命名规则
            filename = Path(parsed.path).name.lower()
            if any(keyword in filename for keyword in preview_keywords):
                return True
            
            return True  # 默认认为有效
            
        except Exception:
            return False
    
    def download_preview_video(self, preview_url: str, video_code: str = None, 
                             output_dir: str = None, enable_cache: bool = True) -> Dict:
        """
        下载预览视频
        
        Args:
            preview_url: 预览视频URL
            video_code: 视频代码（用于命名）
            output_dir: 输出目录
            enable_cache: 是否启用缓存
            
        Returns:
            下载结果字典
        """
        try:
            # 设置输出目录
            if not output_dir:
                output_dir = self.cache_dir / "preview_videos"
            else:
                output_dir = Path(output_dir)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if video_code:
                filename = f"{video_code}_preview"
            else:
                # 从URL生成文件名
                url_hash = hashlib.md5(preview_url.encode()).hexdigest()[:8]
                filename = f"preview_{url_hash}"
            
            # 获取文件扩展名
            parsed_url = urlparse(preview_url)
            ext = Path(parsed_url.path).suffix
            if not ext:
                ext = '.mp4'  # 默认扩展名
            
            output_file = output_dir / f"{filename}{ext}"
            
            # 检查缓存
            if enable_cache and output_file.exists():
                file_size = output_file.stat().st_size
                if file_size > 1024:  # 文件大小大于1KB
                    return {
                        "success": True,
                        "preview_url": preview_url,
                        "output_file": str(output_file),
                        "file_size": file_size,
                        "from_cache": True,
                        "message": "预览视频已存在于缓存中"
                    }
            
            # 下载预览视频
            download_result = self._download_file(preview_url, output_file)
            
            if download_result["success"]:
                return {
                    "success": True,
                    "preview_url": preview_url,
                    "output_file": str(output_file),
                    "file_size": download_result["file_size"],
                    "download_time": download_result["download_time"],
                    "from_cache": False,
                    "message": "预览视频下载成功"
                }
            else:
                return {
                    "success": False,
                    "preview_url": preview_url,
                    "error": download_result["error"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "preview_url": preview_url,
                "error": f"下载预览视频失败: {str(e)}"
            }
    
    def _download_file(self, url: str, output_file: Path) -> Dict:
        """下载文件的核心方法"""
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # 设置请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'video/mp4,video/webm,video/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
                
                # 发送请求
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.download_timeout,
                    stream=True
                )
                response.raise_for_status()
                
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if not any(video_type in content_type for video_type in ['video/', 'application/octet-stream']):
                    # 如果不是视频类型，但文件扩展名是视频格式，仍然尝试下载
                    if not any(url.lower().endswith(ext) for ext in self.supported_formats):
                        return {
                            "success": False,
                            "error": f"URL返回的不是视频内容: {content_type}"
                        }
                
                # 下载文件
                total_size = 0
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                
                # 检查文件大小
                if total_size < 1024:  # 小于1KB可能是错误页面
                    output_file.unlink(missing_ok=True)
                    return {
                        "success": False,
                        "error": f"下载的文件过小: {total_size} bytes"
                    }
                
                download_time = time.time() - start_time
                
                return {
                    "success": True,
                    "file_size": total_size,
                    "download_time": download_time
                }
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"网络请求失败: {str(e)}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"下载失败: {str(e)}"
                }
        
        return {
            "success": False,
            "error": "所有重试都失败了"
        }
    
    def download_all_previews(self, url: str, video_code: str = None, 
                            output_dir: str = None, enable_cache: bool = True) -> Dict:
        """
        下载视频的所有预览视频
        
        Args:
            url: 视频页面URL
            video_code: 视频代码
            output_dir: 输出目录
            enable_cache: 是否启用缓存
            
        Returns:
            下载结果字典
        """
        try:
            # 提取预览视频URL
            extract_result = self.extract_preview_urls(url)
            
            if not extract_result["success"]:
                return extract_result
            
            preview_urls = extract_result["preview_urls"]
            
            if not preview_urls:
                return {
                    "success": True,
                    "url": url,
                    "message": "未找到预览视频",
                    "downloaded_count": 0,
                    "failed_count": 0,
                    "results": []
                }
            
            # 下载所有预览视频
            results = []
            downloaded_count = 0
            failed_count = 0
            
            for i, preview_url in enumerate(preview_urls):
                # 为每个预览视频生成唯一的文件名
                if video_code:
                    current_video_code = f"{video_code}_{i+1}" if len(preview_urls) > 1 else video_code
                else:
                    current_video_code = f"preview_{i+1}"
                
                download_result = self.download_preview_video(
                    preview_url, 
                    current_video_code, 
                    output_dir, 
                    enable_cache
                )
                
                results.append(download_result)
                
                if download_result["success"]:
                    downloaded_count += 1
                else:
                    failed_count += 1
            
            return {
                "success": True,
                "url": url,
                "video_code": video_code,
                "preview_urls": preview_urls,
                "downloaded_count": downloaded_count,
                "failed_count": failed_count,
                "total_count": len(preview_urls),
                "results": results,
                "message": f"预览视频下载完成: 成功{downloaded_count}个，失败{failed_count}个"
            }
            
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": f"批量下载预览视频失败: {str(e)}"
            }
    
    def get_preview_info(self, url: str) -> Dict:
        """
        获取预览视频信息（不下载）
        
        Args:
            url: 视频页面URL
            
        Returns:
            预览视频信息字典
        """
        try:
            # 提取预览视频URL
            extract_result = self.extract_preview_urls(url)
            
            if not extract_result["success"]:
                return extract_result
            
            preview_urls = extract_result["preview_urls"]
            
            # 获取每个预览视频的详细信息
            preview_info = []
            
            for preview_url in preview_urls:
                try:
                    # 发送HEAD请求获取文件信息
                    response = requests.head(preview_url, timeout=10)
                    
                    info = {
                        "url": preview_url,
                        "status_code": response.status_code,
                        "content_type": response.headers.get('content-type', ''),
                        "content_length": response.headers.get('content-length', ''),
                        "last_modified": response.headers.get('last-modified', ''),
                        "accessible": response.status_code == 200
                    }
                    
                    # 估算文件大小
                    if info["content_length"]:
                        try:
                            size_bytes = int(info["content_length"])
                            if size_bytes > 1024 * 1024:
                                info["file_size"] = f"{size_bytes / (1024 * 1024):.2f} MB"
                            elif size_bytes > 1024:
                                info["file_size"] = f"{size_bytes / 1024:.2f} KB"
                            else:
                                info["file_size"] = f"{size_bytes} bytes"
                        except ValueError:
                            info["file_size"] = "未知"
                    else:
                        info["file_size"] = "未知"
                    
                    preview_info.append(info)
                    
                except Exception as e:
                    preview_info.append({
                        "url": preview_url,
                        "error": str(e),
                        "accessible": False
                    })
            
            return {
                "success": True,
                "url": url,
                "preview_count": len(preview_urls),
                "preview_info": preview_info,
                "accessible_count": sum(1 for info in preview_info if info.get("accessible", False))
            }
            
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": f"获取预览视频信息失败: {str(e)}"
            }
    
    def format_preview_response(self, result: Dict) -> str:
        """格式化预览视频响应为文本"""
        if not result.get("success"):
            return f"预览视频操作失败: {result.get('error', '未知错误')}"
        
        response_text = "### MissAV 预览视频信息 ###\n\n"
        
        if "downloaded_count" in result:
            # 下载结果
            response_text += f"**视频URL**: {result.get('url', '')}\n"
            if result.get('video_code'):
                response_text += f"**视频代码**: {result['video_code']}\n"
            
            response_text += f"**预览视频数量**: {result.get('total_count', 0)}\n"
            response_text += f"**下载成功**: {result.get('downloaded_count', 0)}\n"
            response_text += f"**下载失败**: {result.get('failed_count', 0)}\n\n"
            
            if result.get('results'):
                response_text += "**下载详情**:\n"
                for i, download_result in enumerate(result['results'], 1):
                    if download_result.get('success'):
                        file_size = download_result.get('file_size', 0)
                        size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
                        cache_status = " (缓存)" if download_result.get('from_cache') else ""
                        response_text += f"  {i}. ✅ {Path(download_result['output_file']).name} ({size_mb:.2f}MB){cache_status}\n"
                    else:
                        response_text += f"  {i}. ❌ 下载失败: {download_result.get('error', '未知错误')}\n"
        
        elif "preview_info" in result:
            # 信息查询结果
            response_text += f"**视频URL**: {result.get('url', '')}\n"
            response_text += f"**预览视频数量**: {result.get('preview_count', 0)}\n"
            response_text += f"**可访问数量**: {result.get('accessible_count', 0)}\n\n"
            
            if result.get('preview_info'):
                response_text += "**预览视频详情**:\n"
                for i, info in enumerate(result['preview_info'], 1):
                    if info.get('accessible'):
                        response_text += f"  {i}. ✅ {info.get('file_size', '未知大小')} - {info['url']}\n"
                        if info.get('content_type'):
                            response_text += f"      类型: {info['content_type']}\n"
                    else:
                        response_text += f"  {i}. ❌ 不可访问 - {info['url']}\n"
                        if info.get('error'):
                            response_text += f"      错误: {info['error']}\n"
        
        else:
            # 基础提取结果
            response_text += f"**视频URL**: {result.get('url', '')}\n"
            response_text += f"**预览视频数量**: {result.get('preview_count', 0)}\n\n"
            
            if result.get('preview_urls'):
                response_text += "**预览视频URL**:\n"
                for i, url in enumerate(result['preview_urls'], 1):
                    response_text += f"  {i}. {url}\n"
        
        response_text += f"\n{result.get('message', '操作完成')}"
        
        return response_text


def test_preview_downloader():
    """测试预览视频下载器"""
    print("🎬 测试预览视频下载器")
    print("=" * 50)
    
    downloader = PreviewDownloader()
    
    # 测试URL模式匹配
    test_content = '''
    <script>
    var preview = "https://example.com/preview.mp4";
    var hoverVideo = "/videos/hover_video.webm";
    </script>
    <div data-preview="https://example.com/sample.mp4"></div>
    '''
    
    result = downloader.extract_preview_urls("https://example.com/video", test_content)
    print("URL提取测试:")
    print(f"  成功: {result['success']}")
    print(f"  找到URL数量: {result.get('preview_count', 0)}")
    if result.get('preview_urls'):
        for url in result['preview_urls']:
            print(f"    - {url}")
    
    print("\n✅ 预览视频下载器模块已创建")


if __name__ == "__main__":
    test_preview_downloader()