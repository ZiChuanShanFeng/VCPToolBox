#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 异步下载模块
"""

import sys
import json
import os
import uuid
import threading
import traceback
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from .crawler import MissAVCrawler  # 复用已有的下载器逻辑
try:
    from progress_tracker import ProgressTracker
except ImportError:
    from .progress_handler import ProgressHandler as ProgressTracker


class MissAVAsyncDownloader:
    """MissAV 异步下载器"""
    
    def __init__(self):
        self.crawler = MissAVCrawler()
    
    def start_async_download(self, request_data: dict):
        """处理异步下载请求"""
        url = request_data.get('url')
        if not url:
            # 立即返回错误给服务器
            print(json.dumps({"status": "error", "error": "Missing url parameter."}))
            return

        # 提取可选参数
        quality = request_data.get('quality')
        download_dir = request_data.get('download_dir')
        downloader = request_data.get('downloader')

        # 生成唯一的 taskId
        task_id = str(uuid.uuid4())
        
        # 预获取视频标题，并保存会话状态
        video_title = "未知视频"
        core_session = None
        
        try:
            from base_api import BaseCore
            from .consts import HEADERS
            from .missav_api import Video
            
            # 创建会话并获取视频信息
            core_session = BaseCore()
            core_session.config.headers = HEADERS
            core_session.initialize_session()
            
            temp_video = Video(url, core=core_session)
            if temp_video.content:
                video_title = temp_video.title
        except Exception:
            video_title = "未知视频"
            core_session = None

        # 立即返回初始响应
        initial_response = {
            "status": "success",
            "result": {
                "message": f"已开始在后台下载视频 '{video_title}'。任务ID: {task_id}。你可以使用占位符 `{{{{VCP_ASYNC_RESULT::MissAVCrawl::{task_id}}}}}` 来跟踪此任务的进度。",
                "taskId": task_id,
                "placeholder": f"{{{{VCP_ASYNC_RESULT::MissAVCrawl::{task_id}}}}}"
            }
        }
        print(json.dumps(initial_response))
        sys.stdout.flush() # 确保响应被立即发送

        # 启动后台下载线程，传递已建立的会话
        tracker = ProgressTracker(plugin_name="MissAVCrawl", task_id=task_id, video_title=video_title)
        
        download_thread = threading.Thread(
            target=self._download_task,
            args=(url, quality, download_dir, downloader, tracker, core_session)
        )
        download_thread.daemon = False  # 不设置为守护线程，让它独立运行
        download_thread.start()
        
        # 给线程更多时间启动和初始化
        import time
        time.sleep(0.5)
    
    def _download_task(self, url: str, quality: str, download_dir: str, downloader: str, tracker: ProgressTracker, core_session=None):
        """后台下载线程执行的函数 - 重用已建立的会话"""
        try:
            # 设置环境变量（如果未设置）
            import os
            if not os.getenv("VCP_ASYNC_RESULTS_DIR"):
                os.environ["VCP_ASYNC_RESULTS_DIR"] = "./VCPAsyncResults"
            if not os.getenv("CALLBACK_BASE_URL"):
                os.environ["CALLBACK_BASE_URL"] = "http://localhost:8080/callback"
            
            # 启动进度跟踪
            tracker.start()
            
            from .missav_api import Video
            
            # 使用已建立的会话或创建新会话
            if core_session:
                # 重用已建立的会话
                video = Video(url, core=core_session)
            else:
                # 创建新会话（备用方案）
                from base_api import BaseCore
                from .consts import HEADERS
                
                core = BaseCore()
                core.config.headers = HEADERS
                core.initialize_session()
                video = Video(url, core=core)
            
            if not video or not video.content:
                tracker.error("无法获取视频页面内容，请检查网络连接或URL")
                return
            
            # 设置下载参数
            quality = quality or "best"
            download_dir = download_dir or "./downloads"
            downloader = downloader or "threaded"
            
            # 确保下载目录存在
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            
            # 创建进度回调（和调试脚本完全一样）
            def thread_callback(current, total, **kwargs):
                if total > 0:
                    tracker.update(current, total)
            
            # 执行下载（和调试脚本完全一样）
            success = video.download(
                quality=quality,
                downloader=downloader,
                path=str(download_dir),  # 确保是字符串
                callback=thread_callback
            )
            
            if success:
                # 检查实际下载的文件
                files = list(Path(download_dir).glob("*.mp4"))
                if files:
                    for file in files:
                        if file.name.startswith(video.video_code) or video.video_code in file.name:
                            tracker.complete(str(file.absolute()))
                            return
                    # 如果没找到匹配的文件，使用第一个
                    tracker.complete(str(files[0].absolute()))
                else:
                    tracker.error("下载成功但未找到文件")
            else:
                tracker.error("下载过程返回失败状态")

        except Exception as e:
            error_msg = f"下载线程出现异常: {str(e)}"
            tracker.error(error_msg)
            # 添加详细的错误信息用于调试
            import traceback
            print(f"[AsyncDownloader] 详细错误: {traceback.format_exc()}", file=sys.stderr)
    
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



def handle_async_download(request_data: dict):
    """处理异步下载请求的入口函数"""
    downloader = MissAVAsyncDownloader()
    downloader.start_async_download(request_data)


def main():
    """主函数 - 用于直接测试"""
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            print(json.dumps({"status": "error", "error": "No input data received for testing."}), file=sys.stderr)
            return

        request_data = json.loads(input_data)
        command = request_data.get('command')

        if command == "DownloadVideoAsync":
            handle_async_download(request_data)
        else:
            print(json.dumps({"status": "error", "error": f"This script only tests DownloadVideoAsync. Received: {command}"}))

    except Exception as e:
        error_response = {
            "status": "error",
            "error": f"插件测试执行失败: {str(e)}",
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_response))


if __name__ == "__main__":
    main()