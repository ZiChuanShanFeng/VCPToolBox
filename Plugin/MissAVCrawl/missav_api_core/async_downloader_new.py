#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新的异步下载器 - 修复版本
"""

import asyncio
import aiohttp
import aiofiles
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
import sys

# 添加父目录到路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from base_api import BaseCore

class AsyncDownloader:
    """异步下载器"""
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 30, retry_count: int = 3):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.retry_count = retry_count
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def download_segment_async(self, session: aiohttp.ClientSession, url: str, 
                                   output_path: Path, segment_index: int) -> bool:
        """异步下载单个分段"""
        async with self.semaphore:
            for attempt in range(self.retry_count):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # 异步写入文件
                            segment_file = output_path / f"segment_{segment_index:04d}.ts"
                            async with aiofiles.open(segment_file, 'wb') as f:
                                await f.write(content)
                            
                            return True
                        else:
                            print(f"❌ 分段 {segment_index} HTTP错误: {response.status}")
                            
                except Exception as e:
                    print(f"⚠️ 分段 {segment_index} 下载失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(1)
            
            return False
    
    async def download_video_async(self, video, quality: str = "worst", 
                                 output_path: str = "./downloads",
                                 progress_callback: Optional[Callable] = None) -> bool:
        """异步下载视频"""
        try:
            # 获取视频分段
            segments = video.get_segments(quality)
            if not segments:
                print("❌ 无法获取视频分段")
                return False
            
            print(f"📺 开始异步下载: {video.title}")
            print(f"🔗 分段数量: {len(segments)}")
            
            # 创建输出目录
            output_dir = Path(output_path)
            temp_dir = output_dir / f"temp_{video.video_code}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建异步HTTP会话
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                # 创建下载任务
                tasks = []
                for i, segment_url in enumerate(segments):
                    task = self.download_segment_async(session, segment_url, temp_dir, i)
                    tasks.append(task)
                
                # 执行异步下载
                start_time = time.time()
                completed = 0
                
                for task in asyncio.as_completed(tasks):
                    success = await task
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(segments))
                    
                    if completed % 10 == 0 or completed == len(segments):
                        elapsed = time.time() - start_time
                        speed = completed / elapsed if elapsed > 0 else 0
                        print(f"   进度: {completed}/{len(segments)} ({speed:.1f} 分段/秒)")
            
            # 合并分段
            print("🔄 合并视频分段...")
            output_file = output_dir / f"{video.video_code}.mp4"
            
            # 使用ffmpeg合并（如果可用）
            success = await self._merge_segments_ffmpeg(temp_dir, output_file)
            
            if not success:
                # 备用方案：简单合并
                success = await self._merge_segments_simple(temp_dir, output_file)
            
            # 清理临时文件
            if success:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"✅ 下载完成: {output_file}")
            
            return success
            
        except Exception as e:
            print(f"❌ 异步下载失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _merge_segments_ffmpeg(self, temp_dir: Path, output_file: Path) -> bool:
        """使用ffmpeg合并分段"""
        try:
            import subprocess
            
            # 创建文件列表
            file_list = temp_dir / "filelist.txt"
            segments = sorted(temp_dir.glob("segment_*.ts"))
            
            with open(file_list, 'w') as f:
                for segment in segments:
                    f.write(f"file '{segment.absolute()}'\n")
            
            # 使用ffmpeg合并
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(file_list),
                '-c', 'copy',
                str(output_file),
                '-y'  # 覆盖输出文件
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True
            else:
                print(f"⚠️ ffmpeg合并失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"⚠️ ffmpeg不可用: {str(e)}")
            return False
    
    async def _merge_segments_simple(self, temp_dir: Path, output_file: Path) -> bool:
        """简单合并分段"""
        try:
            segments = sorted(temp_dir.glob("segment_*.ts"))
            
            async with aiofiles.open(output_file, 'wb') as outfile:
                for segment in segments:
                    async with aiofiles.open(segment, 'rb') as infile:
                        content = await infile.read()
                        await outfile.write(content)
            
            return True
            
        except Exception as e:
            print(f"❌ 简单合并失败: {str(e)}")
            return False
    
    async def batch_download_async(self, urls: List[str], quality: str = "worst",
                                 output_path: str = "./downloads") -> Dict[str, bool]:
        """批量异步下载"""
        results = {}
        
        try:
            from missav_api_core.missav_api import Video
            
            # 创建核心
            core = BaseCore()
            core.initialize_session()
            
            for url in urls:
                try:
                    print(f"\n🎯 处理视频: {url}")
                    
                    # 创建视频对象
                    video = Video(url, core=core)
                    
                    # 异步下载
                    success = await self.download_video_async(video, quality, output_path)
                    results[url] = success
                    
                except Exception as e:
                    print(f"❌ 处理视频失败 {url}: {str(e)}")
                    results[url] = False
            
            # 清理
            core.close()
            
        except Exception as e:
            print(f"❌ 批量下载失败: {str(e)}")
            for url in urls:
                results[url] = False
        
        return results