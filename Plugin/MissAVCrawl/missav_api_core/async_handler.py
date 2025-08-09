#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV异步下载处理器 - 符合VCP异步插件标准
"""

import sys
import json
import os
import time
import uuid
import threading
import requests
import traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 添加当前目录到路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from base_api import BaseCore
from missav_api_core.consts import HEADERS
from missav_api_core.missav_api import Video
from missav_api_core.subtitle_downloader import SubtitleDownloader, extract_video_code_from_title_or_url

# 常量
LOG_FILE = "MissAVDownloadHistory.log"
PLUGIN_NAME_FOR_CALLBACK = "MissAVCrawl"

def log_event(level, message, data=None):
    """记录日志事件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{level.upper()}] {message}"
    if data:
        try:
            log_entry += f" | Data: {json.dumps(data, ensure_ascii=False)}"
        except Exception:
            log_entry += f" | Data: [Unserializable Data]"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)

def print_json_output(status, result=None, error=None, ai_message=None):
    """输出JSON结果到标准输出"""
    output = {"status": status}
    if status == "success":
        if result is not None:
            output["result"] = result
        if ai_message:
            output["messageForAI"] = ai_message
    elif status == "error":
        if error is not None:
            output["error"] = error
    print(json.dumps(output, ensure_ascii=False))
    log_event("debug", "Output sent to stdout", output)

def update_async_result_file(task_id, status, message, additional_data=None):
    """更新VCPAsyncResults文件"""
    try:
        # 构造结果数据
        result_data = {
            "requestId": task_id,
            "status": status,
            "pluginName": PLUGIN_NAME_FOR_CALLBACK,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加额外数据
        if additional_data:
            result_data.update(additional_data)
        
        # 确保VCPAsyncResults目录存在
        results_dir = Path("../../VCPAsyncResults")
        results_dir.mkdir(exist_ok=True)
        
        # 写入结果文件
        result_file = results_dir / f"{PLUGIN_NAME_FOR_CALLBACK}-{task_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        log_event("debug", f"[{task_id}] Updated async result file", {
            "status": status,
            "file_path": str(result_file)
        })
        
    except Exception as e:
        log_event("error", f"[{task_id}] Failed to update async result file", {
            "error": str(e)
        })

def download_video_background(url, quality, download_dir, task_id, callback_base_url):
    """后台下载视频的函数"""
    log_event("info", f"[{task_id}] Starting background video download", {
        "url": url,
        "quality": quality,
        "download_dir": download_dir
    })
    
    # 初始状态：开始下载
    update_async_result_file(
        task_id, 
        "InProgress", 
        "🔄 任务启动\n\n📡 正在获取视频信息...\n\nℹ️ 系统正在后台处理，无需人工干预。",
        {"videoUrl": url, "quality": quality}
    )
    
    try:
        # 创建核心和视频对象
        core = BaseCore()
        core.config.headers = HEADERS
        core.initialize_session()
        
        video = Video(url, core=core)
        
        # 获取视频信息
        video_title = video.title
        video_code = video.video_code
        
        if not video_title or not video_code:
            raise Exception("无法获取视频信息，可能是视频链接无效或网络问题")
        
        log_event("info", f"[{task_id}] Video info retrieved", {
            "title": video_title,
            "video_code": video_code
        })
        
        # 更新状态：获取到视频信息
        update_async_result_file(
            task_id,
            "InProgress",
            f"📺 视频信息已获取\n\n🎬 {video_title}\n🆔 {video_code}\n\n🔄 正在解析视频分段...\n\nℹ️ 系统正在后台处理，无需人工干预。",
            {
                "videoTitle": video_title,
                "videoCode": video_code,
                "videoUrl": url,
                "quality": quality
            }
        )
        
        # 获取分段信息
        segments = video.get_segments(quality)
        total_segments = len(segments) if segments else 0
        
        if total_segments == 0:
            raise Exception("无法获取视频分段信息，可能是视频不存在或质量设置不正确")
        
        if total_segments > 0:
            # 更新状态：开始下载分段
            update_async_result_file(
                task_id,
                "InProgress", 
                f"🔗 分段解析完成\n\n📺 {video_title}\n🆔 {video_code}\n📊 总分段: {total_segments}\n\n⬇️ 开始下载...\n\nℹ️ 系统正在后台下载，无需人工干预。",
                {
                    "videoTitle": video_title,
                    "videoCode": video_code,
                    "videoUrl": url,
                    "quality": quality,
                    "totalSegments": total_segments,
                    "currentSegment": 0,
                    "progress": 0
                }
            )
        
        # 创建下载目录
        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)
        
        # 下载视频 - 带实时进度更新
        # 提前提取视频番号，准备同步字幕下载
        extracted_video_code = extract_video_code_from_title_or_url(video_title, url)
        if not extracted_video_code:
            extracted_video_code = video_code  # 使用原始video_code作为备选
        
        # 字幕下载状态共享变量（在进度回调中需要访问）
        subtitle_result = {"status": "searching", "success": False, "message": "", "info": {}}
        
        # 初始化进度跟踪变量
        # 从配置中获取更新间隔，默认10秒
        update_interval = float(os.getenv('MISSAV_PROGRESS_UPDATE_INTERVAL', '10'))
        segment_update_interval = int(os.getenv('MISSAV_SEGMENT_UPDATE_INTERVAL', '25'))
        
        progress_state = {
            'start_time': time.time(),
            'last_update_time': 0,
            'update_interval': update_interval,  # 可配置的更新间隔
            'segment_interval': segment_update_interval  # 可配置的分段间隔
        }
        
        def progress_callback(current, total, **kwargs):
            """真实的下载进度回调 - 这是唯一的进度报告点"""
            if total > 0:
                progress = (current / total) * 100
                current_time = time.time()
                
                # 控制更新频率：每N个分段或每N秒或完成时更新
                should_update = (
                    current % progress_state['segment_interval'] == 0 or 
                    current == total or 
                    (current_time - progress_state['last_update_time']) >= progress_state['update_interval']
                )
                
                if should_update:
                    progress_state['last_update_time'] = current_time
                    
                    log_event("info", f"[{task_id}] Real download progress: {progress:.1f}% ({current}/{total})")
                    
                    # 计算预计剩余时间（基于真实的下载进度）
                    elapsed_time = current_time - progress_state['start_time']
                    if current > 0 and elapsed_time > 0:
                        avg_time_per_segment = elapsed_time / current
                        remaining_segments = total - current
                        estimated_remaining_time = avg_time_per_segment * remaining_segments
                        
                        if estimated_remaining_time > 60:
                            time_str = f"约 {estimated_remaining_time/60:.1f} 分钟"
                        else:
                            time_str = f"约 {estimated_remaining_time:.0f} 秒"
                    else:
                        time_str = "计算中..."
                    
                    # 获取字幕下载状态
                    subtitle_status_text = ""
                    if subtitle_result["status"] == "searching":
                        subtitle_status_text = "🔍 字幕搜索中..."
                    elif subtitle_result["status"] == "completed":
                        if subtitle_result["success"]:
                            subtitle_status_text = f"✅ 字幕: {subtitle_result['message']}"
                        else:
                            subtitle_status_text = "❌ 字幕下载失败"
                    elif subtitle_result["status"] == "error":
                        subtitle_status_text = "⚠️ 字幕下载出错"
                    
                    # 实时更新VCPAsyncResults文件
                    update_async_result_file(
                        task_id,
                        "InProgress",
                        f"📥 下载中: {progress:.1f}% ({current}/{total})\n"
                        f"📺 {video_title} ({video_code})\n"
                        f"⏱️ 剩余: {time_str}\n"
                        f"{subtitle_status_text}",
                        {
                            "videoTitle": video_title,
                            "videoCode": video_code,
                            "videoUrl": url,
                            "quality": quality,
                            "totalSegments": total,
                            "currentSegment": current,
                            "progress": round(progress, 1),
                            "estimatedRemainingTime": time_str,
                            "downloadSpeed": f"{current/elapsed_time:.1f} 分段/秒" if elapsed_time > 0 else "计算中...",
                            "subtitleStatus": subtitle_result.get("status", "unknown")
                        }
                    )
        
        # 字幕下载线程变量
        subtitle_thread = None
        
        # 启动字幕下载线程（与视频下载并行）
        def subtitle_download_worker():
            try:
                log_event("info", f"[{task_id}] Starting parallel subtitle download", {
                    "original_video_code": video_code,
                    "extracted_video_code": extracted_video_code,
                    "video_title": video_title
                })
                
                # 更新字幕搜索状态
                subtitle_result["status"] = "searching"
                
                # 创建字幕下载器
                subtitle_downloader = SubtitleDownloader()
                
                # 预估的字幕输出目录（与视频文件同目录）
                subtitle_output_dir = str(download_path)
                
                # 生成字幕文件基础名（基于视频标题和代码）
                clean_title = video_title.replace('/', '_').replace('\\', '_')
                subtitle_filename_base = f"{extracted_video_code}_{clean_title[:30]}"
                
                # 下载字幕
                subtitle_success, subtitle_message = subtitle_downloader.download_subtitle(
                    extracted_video_code, 
                    subtitle_output_dir, 
                    subtitle_filename_base
                )
                
                # 更新结果
                subtitle_result["success"] = subtitle_success
                subtitle_result["message"] = subtitle_message
                subtitle_result["status"] = "completed"
                
                if subtitle_success:
                    subtitle_result["info"] = {
                        "status": "success",
                        "source": subtitle_message,
                        "videoCode": extracted_video_code
                    }
                    log_event("success", f"[{task_id}] Parallel subtitle download successful", {
                        "video_code": extracted_video_code,
                        "source": subtitle_message
                    })
                else:
                    subtitle_result["info"] = {
                        "status": "failed",
                        "error": subtitle_message,
                        "videoCode": extracted_video_code
                    }
                    log_event("warning", f"[{task_id}] Parallel subtitle download failed", {
                        "video_code": extracted_video_code,
                        "error": subtitle_message
                    })
                    
            except Exception as subtitle_error:
                subtitle_result["status"] = "error"
                subtitle_result["success"] = False
                subtitle_result["message"] = f"字幕下载出错: {str(subtitle_error)}"
                subtitle_result["info"] = {
                    "status": "error",
                    "error": f"字幕下载出错: {str(subtitle_error)}",
                    "videoCode": extracted_video_code
                }
                log_event("error", f"[{task_id}] Parallel subtitle download error", {
                    "error": str(subtitle_error),
                    "traceback": traceback.format_exc()
                })
        
        # 启动字幕下载线程
        subtitle_thread = threading.Thread(target=subtitle_download_worker, daemon=True)
        subtitle_thread.start()
        
        # 开始视频下载（与字幕下载并行）
        success = video.download(
            quality=quality,
            downloader="threaded",
            path=str(download_path),
            callback=progress_callback,
            no_title=True  # 重要：设置为True，避免路径被修改
        )
        
        if success:
            # 查找下载的文件 - 改进文件查找逻辑，支持递归查找
            video_files = []
            
            # 首先尝试按视频代码查找（直接在下载目录）
            video_files = list(download_path.glob(f"*{video_code}*.mp4"))
            
            # 如果没找到，尝试按标题查找
            if not video_files:
                clean_title = video_title.replace('/', '_').replace('\\', '_')
                truncated_title = clean_title[:50] if len(clean_title) > 50 else clean_title
                video_files = list(download_path.glob(f"*{truncated_title}*.mp4"))
            
            # 如果还没找到，查找所有mp4文件
            if not video_files:
                video_files = list(download_path.glob("*.mp4"))
            
            # 如果仍然没找到，尝试递归查找（处理嵌套目录的情况）
            if not video_files:
                log_event("info", f"[{task_id}] No files found in root, trying recursive search")
                
                # 递归查找所有.mp4文件
                video_files = list(download_path.rglob("*.mp4"))
                
                # 如果找到了嵌套文件，尝试移动到根目录
                if video_files:
                    log_event("warning", f"[{task_id}] Found nested video files, attempting to fix", {
                        "nested_files": [str(f) for f in video_files]
                    })
                    
                    fixed_files = []
                    for nested_file in video_files:
                        if nested_file.parent != download_path:
                            # 文件在子目录中，尝试移动到根目录
                            try:
                                new_path = download_path / nested_file.name
                                
                                # 如果目标文件已存在，生成新名称
                                counter = 1
                                while new_path.exists():
                                    name_parts = nested_file.stem, counter, nested_file.suffix
                                    new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                                    new_path = download_path / new_name
                                    counter += 1
                                
                                # 移动文件
                                import shutil
                                shutil.move(str(nested_file), str(new_path))
                                fixed_files.append(new_path)
                                
                                log_event("info", f"[{task_id}] Moved nested file", {
                                    "from": str(nested_file),
                                    "to": str(new_path)
                                })
                                
                                # 尝试删除空的父目录
                                try:
                                    if nested_file.parent != download_path and not list(nested_file.parent.iterdir()):
                                        nested_file.parent.rmdir()
                                        log_event("info", f"[{task_id}] Removed empty directory: {nested_file.parent}")
                                except Exception:
                                    pass
                                    
                            except Exception as move_error:
                                log_event("error", f"[{task_id}] Failed to move nested file", {
                                    "file": str(nested_file),
                                    "error": str(move_error)
                                })
                                fixed_files.append(nested_file)  # 保留原位置
                        else:
                            fixed_files.append(nested_file)
                    
                    video_files = fixed_files
            
            # 过滤掉目录（确保只有文件）
            video_files = [f for f in video_files if f.is_file()]
            
            if video_files:
                # 选择最新的文件（按修改时间）
                video_file = max(video_files, key=lambda f: f.stat().st_mtime)
                
                log_event("info", f"[{task_id}] Found video file", {
                    "file_path": str(video_file),
                    "file_size_bytes": video_file.stat().st_size,
                    "all_found_files": [str(f) for f in video_files]
                })
                
                # 检查文件是否真实存在且有内容
                if not video_file.exists():
                    raise Exception(f"下载的视频文件不存在: {video_file}")
                
                if video_file.is_dir():
                    raise Exception(f"找到的是目录而不是文件: {video_file}")
                
                # 更准确的文件大小计算
                file_size_bytes = video_file.stat().st_size
                file_size_mb = file_size_bytes / (1024 * 1024)  # MB
                file_size_gb = file_size_bytes / (1024 * 1024 * 1024)  # GB
                
                # 根据文件大小选择合适的显示单位
                if file_size_gb >= 1.0:
                    file_size_display = f"{file_size_gb:.2f} GB"
                else:
                    file_size_display = f"{file_size_mb:.2f} MB"
                
                log_event("info", f"[{task_id}] File size check", {
                    "file_path": str(video_file),
                    "file_size_bytes": file_size_bytes,
                    "file_size_mb": file_size_mb,
                    "file_size_display": file_size_display,
                    "is_file": video_file.is_file(),
                    "is_dir": video_file.is_dir()
                })
                
                # 从配置中获取最小文件大小
                min_file_size = float(os.getenv('MISSAV_MIN_FILE_SIZE_MB', '0.5'))
                
                # 验证文件大小是否合理
                if file_size_mb < min_file_size:  # 如果文件小于配置的最小大小，认为下载失败
                    raise Exception(f"下载的文件过小({file_size_display} < {min_file_size}MB)，可能下载失败或文件损坏")
                
                # 验证文件是否为有效的视频文件（简单检查文件头）
                try:
                    with open(video_file, 'rb') as f:
                        file_header = f.read(8)
                        # 检查是否为有效的MP4文件头
                        if len(file_header) < 8:
                            raise Exception("文件头不完整，文件可能损坏")
                        # 简单的MP4文件头检查（不是完整验证，但能检测明显的问题）
                        if file_header[4:8] not in [b'ftyp', b'mdat', b'moov']:
                            log_event("warning", f"[{task_id}] 文件可能不是有效的MP4格式", {
                                "file_header": file_header.hex()
                            })
                except Exception as header_check_error:
                    log_event("warning", f"[{task_id}] 文件头检查失败: {str(header_check_error)}")
                
                # 获取视频时长信息（如果可能）
                try:
                    import subprocess
                    # 尝试使用 ffprobe 获取视频信息
                    result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                        '-show_format', '-show_streams', str(video_file)
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        import json as json_lib
                        probe_data = json_lib.loads(result.stdout)
                        duration = float(probe_data.get('format', {}).get('duration', 0))
                        
                        # 格式化时长
                        if duration > 0:
                            hours = int(duration // 3600)
                            minutes = int((duration % 3600) // 60)
                            seconds = int(duration % 60)
                            if hours > 0:
                                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                            else:
                                duration_str = f"{minutes:02d}:{seconds:02d}"
                        else:
                            duration_str = "未知"
                        
                        # 获取视频分辨率
                        video_stream = next((s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video'), {})
                        width = video_stream.get('width', 0)
                        height = video_stream.get('height', 0)
                        resolution_str = f"{width}x{height}" if width and height else "未知"
                        
                    else:
                        duration_str = "未知"
                        resolution_str = "未知"
                        
                except Exception as probe_error:
                    log_event("warning", f"[{task_id}] Failed to probe video info: {str(probe_error)}")
                    duration_str = "未知"
                    resolution_str = "未知"
                
                # 等待并行字幕下载完成
                subtitle_status = "未尝试"
                subtitle_info = {}
                
                try:
                    # 检查字幕下载状态
                    if subtitle_thread and subtitle_thread.is_alive():
                        # 更新状态：等待字幕下载完成
                        update_async_result_file(
                            task_id,
                            "InProgress",
                            f"📥 视频下载完成，等待字幕下载完成...\n"
                            f"📺 {video_title} ({video_code})\n"
                            f"📁 {video_file.name}\n"
                            f"📊 {file_size_display}\n"
                            f"🔍 字幕状态: {subtitle_result['status']}",
                            {
                                "videoTitle": video_title,
                                "videoCode": video_code,
                                "videoUrl": url,
                                "filePath": str(video_file),
                                "fileName": video_file.name,
                                "fileSize": file_size_display,
                                "fileSizeBytes": file_size_bytes,
                                "resolution": resolution_str,
                                "duration": duration_str,
                                "quality": quality,
                                "progress": 100,
                                "totalSegments": total_segments,
                                "subtitleStatus": subtitle_result["status"]
                            }
                        )
                        
                        # 等待字幕下载完成（最多等待30秒）
                        subtitle_thread.join(timeout=30)
                    
                    # 获取字幕下载结果
                    if subtitle_result["success"]:
                        subtitle_status = "成功"
                        subtitle_info = subtitle_result["info"]
                        
                        # 如果字幕文件名与视频文件名不匹配，尝试重命名
                        try:
                            # 查找下载的字幕文件
                            subtitle_files = list(download_path.glob(f"*{extracted_video_code}*.srt")) + \
                                           list(download_path.glob(f"*{extracted_video_code}*.ass"))
                            
                            if subtitle_files:
                                subtitle_file = subtitle_files[0]  # 取第一个找到的字幕文件
                                expected_subtitle_name = f"{video_file.stem}{subtitle_file.suffix}"
                                expected_subtitle_path = video_file.parent / expected_subtitle_name
                                
                                # 如果字幕文件名与视频文件名不匹配，重命名
                                if subtitle_file.name != expected_subtitle_name:
                                    import shutil
                                    shutil.move(str(subtitle_file), str(expected_subtitle_path))
                                    log_event("info", f"[{task_id}] Renamed subtitle file", {
                                        "from": str(subtitle_file),
                                        "to": str(expected_subtitle_path)
                                    })
                        except Exception as rename_error:
                            log_event("warning", f"[{task_id}] Failed to rename subtitle file: {str(rename_error)}")
                        
                    elif subtitle_result["status"] == "error":
                        subtitle_status = "错误"
                        subtitle_info = subtitle_result["info"]
                    else:
                        subtitle_status = "失败"
                        subtitle_info = subtitle_result["info"]
                        
                except Exception as subtitle_error:
                    subtitle_status = "错误"
                    subtitle_info = {
                        "status": "error",
                        "error": f"字幕处理出错: {str(subtitle_error)}",
                        "videoCode": extracted_video_code
                    }
                    log_event("error", f"[{task_id}] Subtitle processing error", {
                        "error": str(subtitle_error),
                        "traceback": traceback.format_exc()
                    })
                
                # 最终成功状态 - 更新VCPAsyncResults文件，包含更丰富的信息和字幕状态
                success_message = (
                    f"✅ 下载完成\n\n"
                    f"📺 {video_title}\n"
                    f"🆔 {video_code}\n"
                    f"📁 {video_file.name}\n"
                    f"📊 {file_size_display}\n"
                    f"🎬 分辨率: {resolution_str}\n"
                    f"⏱️ 时长: {duration_str}\n"
                    f"🎯 质量: {quality}\n"
                    f"📂 路径: {str(video_file)}\n"
                    f"📝 字幕: {subtitle_status}"
                )
                
                # 如果字幕下载成功，只添加简单状态
                if subtitle_status == "成功":
                    success_message += f" ({subtitle_info.get('source', '字幕')})"
                
                update_async_result_file(
                    task_id,
                    "Succeed",
                    success_message,
                    {
                        "videoTitle": video_title,
                        "videoCode": video_code,
                        "videoUrl": url,
                        "filePath": str(video_file),
                        "fileName": video_file.name,
                        "fileSize": file_size_display,
                        "fileSizeBytes": file_size_bytes,
                        "resolution": resolution_str,
                        "duration": duration_str,
                        "quality": quality,
                        "progress": 100,
                        "downloadTime": datetime.now().isoformat(),
                        "totalSegments": total_segments,
                        "subtitleStatus": subtitle_status,
                        "subtitleInfo": subtitle_info
                    }
                )
                
                # 构造符合VCP标准的回调数据
                callback_data = {
                    "requestId": task_id,
                    "status": "Succeed",
                    "pluginName": PLUGIN_NAME_FOR_CALLBACK,
                    "type": "missav_download_status",  # 明确指定类型
                    "videoTitle": video_title,
                    "videoCode": video_code,
                    "videoUrl": url,
                    "filePath": str(video_file),
                    "fileName": video_file.name,
                    "fileSize": file_size_display,
                    "fileSizeBytes": file_size_bytes,
                    "resolution": resolution_str,
                    "duration": duration_str,
                    "quality": quality,
                    "totalSegments": total_segments,
                    "downloadTime": datetime.now().isoformat(),
                    "subtitleStatus": subtitle_status,
                    "subtitleInfo": subtitle_info,
                    "message": success_message
                }
                
                log_event("success", f"[{task_id}] Video download completed successfully", {
                    "file_path": str(video_file),
                    "file_size_display": file_size_display,
                    "file_size_bytes": file_size_bytes,
                    "resolution": resolution_str,
                    "duration": duration_str
                })
            else:
                raise Exception("下载完成但未找到视频文件")
        else:
            raise Exception("视频下载失败")
            
    except Exception as e:
        error_str = str(e)
        log_event("error", f"[{task_id}] Video download failed", {
            "error": error_str,
            "traceback": traceback.format_exc()
        })
        
        # 根据错误类型提供更具体的错误信息
        if "过小" in error_str:
            error_detail = "下载的文件过小，可能是网络问题或视频源问题"
        elif "不存在" in error_str:
            error_detail = "下载过程中文件创建失败"
        elif "分段" in error_str:
            error_detail = "视频分段下载失败，可能是网络不稳定"
        elif "truncate" in error_str:
            error_detail = "插件内部错误，请联系开发者"
        else:
            error_detail = error_str
        
        # 失败状态 - 更新VCPAsyncResults文件
        error_message = f"❌ 下载失败\n💥 {error_detail}"
        
        update_async_result_file(
            task_id,
            "Failed",
            error_message,
            {
                "videoUrl": url,
                "quality": quality,
                "error": error_str,
                "errorDetail": error_detail,
                "progress": 0
            }
        )
        
        # 发送失败回调
        callback_data = {
            "requestId": task_id,
            "status": "Failed", 
            "pluginName": PLUGIN_NAME_FOR_CALLBACK,
            "type": "missav_download_status",  # 明确指定类型
            "videoUrl": url,
            "quality": quality,
            "error": error_str,
            "errorDetail": error_detail,
            "message": error_message,
            "downloadTime": datetime.now().isoformat()
        }
    
    # 发送回调 - 确保callback_data已定义
    if 'callback_data' not in locals():
        # 如果callback_data未定义，创建一个基本的失败回调
        callback_data = {
            "requestId": task_id,
            "status": "Failed", 
            "pluginName": PLUGIN_NAME_FOR_CALLBACK,
            "type": "missav_download_status",  # 明确指定类型
            "videoUrl": url,
            "quality": quality,
            "error": "Unknown error occurred",
            "message": "❌ MissAV视频下载失败\n\n未知错误发生",
            "downloadTime": datetime.now().isoformat()
        }
    
    try:
        callback_url = f"{callback_base_url}/{PLUGIN_NAME_FOR_CALLBACK}/{task_id}"
        log_event("info", f"[{task_id}] Sending callback to {callback_url}", {
            "callback_data": callback_data
        })
        
        response = requests.post(callback_url, json=callback_data, timeout=30)
        response.raise_for_status()
        
        log_event("success", f"[{task_id}] Callback sent successfully", {
            "callback_url": callback_url,
            "status_code": response.status_code,
            "response_text": response.text
        })
    except Exception as cb_e:
        log_event("error", f"[{task_id}] Failed to send callback", {
            "callback_url": callback_url if 'callback_url' in locals() else 'undefined',
            "error": str(cb_e),
            "traceback": traceback.format_exc()
        })

def handle_async_download(request_data):
    """处理异步下载请求"""
    # 加载配置
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    # 获取配置
    download_dir = os.getenv("MISSAV_DOWNLOAD_DIR", "./downloads")
    callback_base_url = os.getenv("CALLBACK_BASE_URL")
    
    if not callback_base_url:
        log_event("warning", "CALLBACK_BASE_URL not found in environment variables")
        print_json_output("error", error="CALLBACK_BASE_URL not configured")
        return
    
    # 获取请求参数
    url = request_data.get('url')
    quality = request_data.get('quality', 'best')
    
    if not url:
        print_json_output("error", error="Missing required parameter: url")
        return
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    log_event("info", f"[{task_id}] Async download request received", {
        "url": url,
        "quality": quality,
        "download_dir": download_dir
    })
    
    # 立即返回任务ID和占位符指导
    result_string_for_ai = (
        f"MissAV视频下载任务 (ID: {task_id}) 已成功提交。\n"
        f"视频将在后台下载，这可能需要几分钟时间。\n\n"
        f"**AI指令**：下面的占位符是一个动态状态显示器，会自动更新下载进度推送给你\n"
        f"- 被询问到下载进度时，无特殊说明都默认为询问的是实时的下载进度，\n"
        f"- 不要猜测或描述占位符的内容\n"
        f"- 不要添加额外的进度描述或状态说明\n"
        f"- 系统会自动将占位符替换为实时状态，但是你无法通过输出这段占位符然后得到一个自动替换的结果，占位符是自动推送给你的，你无需主动调用。\n\n"
        f"状态占位符：{{{{VCP_ASYNC_RESULT::MissAVCrawl::{task_id}}}}}"
    )
    
    print_json_output("success", result=result_string_for_ai)
    
    # 启动后台下载线程
    download_thread = threading.Thread(
        target=download_video_background,
        args=(url, quality, download_dir, task_id, callback_base_url)
    )
    download_thread.start()
    
    log_event("info", f"[{task_id}] Background download thread started")