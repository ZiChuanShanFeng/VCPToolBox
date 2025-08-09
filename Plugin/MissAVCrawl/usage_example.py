#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAVCrawl 插件使用示例
展示改进后的功能使用方法
"""

import json

def example_download_request():
    """异步下载请求示例"""
    print("📥 异步下载请求示例:")
    print("=" * 40)
    
    # 模拟 AI 发送的工具调用请求
    request_example = """
<<<[TOOL_REQUEST]>>>
tool_name:「始」MissAVCrawl「末」,
command:「始」DownloadVideoAsync「末」,
url:「始」https://missav.ws/ssis-950「末」,
quality:「始」best「末」
<<<[END_TOOL_REQUEST]>>>
"""
    
    print("AI 工具调用格式:")
    print(request_example)
    
    # 模拟插件返回的初始响应
    initial_response = {
        "status": "success",
        "result": "MissAV视频下载任务 (ID: abc123) 已成功提交。\n视频将在后台下载，这可能需要几分钟时间。\n\n**AI指令**：下面的占位符是一个动态状态显示器，会自动更新下载进度推送给你\n状态占位符：{{VCP_ASYNC_RESULT::MissAVCrawl::abc123}}"
    }
    
    print("\n插件初始响应:")
    print(json.dumps(initial_response, ensure_ascii=False, indent=2))

def example_callback_data():
    """回调数据示例"""
    print("\n📡 WebSocket 回调数据示例:")
    print("=" * 40)
    
    # 进行中状态
    progress_data = {
        "requestId": "abc123",
        "status": "InProgress",
        "pluginName": "MissAVCrawl",
        "type": "missav_download_status",
        "videoTitle": "SSIS-950 美女写真集",
        "videoCode": "SSIS-950",
        "videoUrl": "https://missav.ws/ssis-950",
        "quality": "best",
        "totalSegments": 150,
        "currentSegment": 75,
        "progress": 50.0,
        "estimatedRemainingTime": "约 3 分钟",
        "downloadSpeed": "2.5 分段/秒",
        "message": "📥 下载中: 50.0% (75/150)\n📺 SSIS-950 美女写真集 (SSIS-950)\n⏱️ 剩余: 约 3 分钟"
    }
    
    print("进行中状态:")
    print(json.dumps(progress_data, ensure_ascii=False, indent=2))
    
    # 完成状态
    success_data = {
        "requestId": "abc123",
        "status": "Succeed",
        "pluginName": "MissAVCrawl",
        "type": "missav_download_status",
        "videoTitle": "SSIS-950 美女写真集",
        "videoCode": "SSIS-950",
        "videoUrl": "https://missav.ws/ssis-950",
        "filePath": "/downloads/SSIS-950.mp4",
        "fileName": "SSIS-950.mp4",
        "fileSize": "1.25 GB",
        "fileSizeBytes": 1342177280,
        "resolution": "1920x1080",
        "duration": "02:15:30",
        "quality": "best",
        "totalSegments": 150,
        "downloadTime": "2024-01-01T12:30:00",
        "message": "✅ 下载完成\n\n📺 SSIS-950 美女写真集\n🆔 SSIS-950\n📁 SSIS-950.mp4\n📊 1.25 GB\n🎬 分辨率: 1920x1080\n⏱️ 时长: 02:15:30\n🎯 质量: best\n📂 路径: /downloads/SSIS-950.mp4"
    }
    
    print("\n完成状态:")
    print(json.dumps(success_data, ensure_ascii=False, indent=2))

def example_quality_options():
    """质量选项示例"""
    print("\n🎯 质量参数选项:")
    print("=" * 40)
    
    quality_examples = [
        ("best", "自动选择最高质量（推荐）"),
        ("worst", "选择最低质量（节省空间）"),
        ("1080p", "选择 1080p 分辨率"),
        ("720p", "选择 720p 分辨率"),
        ("480p", "选择 480p 分辨率"),
        ("360p", "选择 360p 分辨率")
    ]
    
    for quality, description in quality_examples:
        print(f"• {quality:8} - {description}")
        
    print("\n使用示例:")
    for quality, _ in quality_examples[:3]:  # 只显示前3个示例
        print(f"""
<<<[TOOL_REQUEST]>>>
tool_name:「始」MissAVCrawl「末」,
command:「始」DownloadVideoAsync「末」,
url:「始」https://missav.ws/example「末」,
quality:「始」{quality}「末」
<<<[END_TOOL_REQUEST]>>>""")

def example_websocket_client():
    """WebSocket 客户端示例"""
    print("\n🔌 前端 WebSocket 连接示例:")
    print("=" * 40)
    
    js_example = """
// JavaScript WebSocket 客户端示例
const ws = new WebSocket('ws://localhost:6005/VCPlog/VCP_Key=your_vcp_key');

ws.onopen = function(event) {
    console.log('WebSocket 连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    // 只处理 MissAV 下载状态消息
    if (data.type === 'missav_download_status') {
        const downloadData = data.data;
        
        console.log('下载状态更新:', downloadData.status);
        console.log('进度:', downloadData.progress + '%');
        console.log('消息:', downloadData.message);
        
        // 根据状态更新 UI
        switch(downloadData.status) {
            case 'InProgress':
                updateProgressBar(downloadData.progress);
                showMessage(downloadData.message, 'info');
                break;
            case 'Succeed':
                showMessage('下载完成！', 'success');
                showVideoInfo(downloadData);
                break;
            case 'Failed':
                showMessage('下载失败：' + downloadData.error, 'error');
                break;
        }
    }
};

function updateProgressBar(progress) {
    document.getElementById('progress').style.width = progress + '%';
    document.getElementById('progress-text').textContent = progress.toFixed(1) + '%';
}

function showVideoInfo(data) {
    document.getElementById('video-title').textContent = data.videoTitle;
    document.getElementById('video-size').textContent = data.fileSize;
    document.getElementById('video-resolution').textContent = data.resolution;
    document.getElementById('video-duration').textContent = data.duration;
}
"""
    
    print(js_example)

def main():
    """主函数"""
    print("🚀 MissAVCrawl 插件使用示例")
    print("=" * 50)
    
    example_download_request()
    example_callback_data()
    example_quality_options()
    example_websocket_client()
    
    print("\n" + "=" * 50)
    print("📚 更多信息请参考:")
    print("• IMPROVEMENTS_SUMMARY.md - 改进详情")
    print("• plugin-manifest.json - 插件配置")
    print("• test_improvements.py - 功能测试")

if __name__ == "__main__":
    main()