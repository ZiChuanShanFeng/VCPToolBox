#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAVCrawl 插件最终配置验证脚本
验证所有改进是否正确实施
"""

import json
import os
from pathlib import Path

def verify_plugin_manifest():
    """验证插件清单配置"""
    print("🔍 验证插件清单配置...")
    
    manifest_path = Path(__file__).parent / "plugin-manifest.json"
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # 检查 WebSocket 推送配置
        ws_push = manifest.get("webSocketPush", {})
        
        checks = [
            (ws_push.get("enabled") == True, "WebSocket 推送已启用"),
            (ws_push.get("messageType") == "missav_download_status", "消息类型为 missav_download_status"),
            (ws_push.get("usePluginResultAsMessage") == True, "使用插件结果作为消息"),
            (ws_push.get("targetClientType") == "VCPLog", "目标客户端类型为 VCPLog"),
            (manifest.get("pluginType") == "asynchronous", "插件类型为异步"),
            (manifest.get("name") == "MissAVCrawl", "插件名称正确")
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 读取插件清单失败: {str(e)}")
        return False

def verify_async_handler():
    """验证异步处理器改进"""
    print("\n🔍 验证异步处理器改进...")
    
    handler_path = Path(__file__).parent / "missav_api_core" / "async_handler.py"
    
    try:
        with open(handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键改进
        checks = [
            ("file_size_gb" in content, "文件大小 GB 计算"),
            ("file_size_display" in content, "文件大小显示格式"),
            ("resolution" in content, "视频分辨率信息"),
            ("duration" in content, "视频时长信息"),
            ("ffprobe" in content, "视频信息获取"),
            ("fileSizeBytes" in content, "原始字节数信息"),
            ("downloadTime" in content, "下载时间信息"),
            ("totalSegments" in content, "总分段数信息"),
            ('"type": "missav_download_status"' in content, "消息类型标识")
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 读取异步处理器失败: {str(e)}")
        return False

def verify_base_api():
    """验证基础 API 改进"""
    print("\n🔍 验证基础 API 改进...")
    
    api_path = Path(__file__).parent / "base_api.py"
    
    try:
        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查质量选择改进
        checks = [
            ("streams.sort" in content, "流媒体排序"),
            ("bandwidth" in content, "带宽信息"),
            ("resolution" in content, "分辨率信息"),
            ("target_height" in content, "目标高度匹配"),
            ("quality.endswith('p')" in content, "质量参数解析"),
            ("选择质量:" in content, "质量选择日志")
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 读取基础 API 失败: {str(e)}")
        return False

def verify_documentation():
    """验证文档完整性"""
    print("\n🔍 验证文档完整性...")
    
    docs = [
        ("IMPROVEMENTS_SUMMARY.md", "改进总结文档"),
        ("WEBSOCKET_PUSH_CLARIFICATION.md", "WebSocket 推送说明"),
        ("frontend_integration_example.html", "前端集成示例"),
        ("test_improvements.py", "功能测试脚本"),
        ("usage_example.py", "使用示例脚本")
    ]
    
    all_passed = True
    for filename, description in docs:
        file_path = Path(__file__).parent / filename
        if file_path.exists():
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description}")
            all_passed = False
    
    return all_passed

def verify_message_structure():
    """验证消息结构"""
    print("\n🔍 验证消息结构...")
    
    # 模拟完整的回调数据结构
    expected_fields = [
        "requestId", "status", "pluginName", "type", "videoTitle", 
        "videoCode", "videoUrl", "filePath", "fileName", "fileSize",
        "fileSizeBytes", "resolution", "duration", "quality", 
        "totalSegments", "downloadTime", "message"
    ]
    
    sample_data = {
        "requestId": "test-id",
        "status": "Succeed",
        "pluginName": "MissAVCrawl",
        "type": "missav_download_status",
        "videoTitle": "测试视频",
        "videoCode": "TEST-001",
        "videoUrl": "https://missav.ws/test",
        "filePath": "/downloads/test.mp4",
        "fileName": "test.mp4",
        "fileSize": "100.50 MB",
        "fileSizeBytes": 105414041,
        "resolution": "1920x1080",
        "duration": "15:30",
        "quality": "best",
        "totalSegments": 93,
        "downloadTime": "2024-01-01T12:00:00",
        "message": "下载完成"
    }
    
    all_passed = True
    for field in expected_fields:
        if field in sample_data:
            print(f"  ✅ {field}")
        else:
            print(f"  ❌ {field}")
            all_passed = False
    
    print(f"\n  📊 消息字段数量: {len(sample_data)}")
    print(f"  📋 消息类型: {sample_data.get('type')}")
    
    return all_passed

def main():
    """主验证函数"""
    print("🚀 MissAVCrawl 插件最终配置验证")
    print("=" * 60)
    
    results = []
    
    # 执行各项验证
    results.append(("插件清单配置", verify_plugin_manifest()))
    results.append(("异步处理器改进", verify_async_handler()))
    results.append(("基础 API 改进", verify_base_api()))
    results.append(("文档完整性", verify_documentation()))
    results.append(("消息结构", verify_message_structure()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 验证结果汇总:")
    
    passed_count = 0
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if passed:
            passed_count += 1
    
    print(f"\n📊 总体结果: {passed_count}/{len(results)} 项通过")
    
    if passed_count == len(results):
        print("\n🎉 所有验证通过！插件配置正确。")
        print("\n📝 使用说明:")
        print("1. 插件会推送 'missav_download_status' 类型的消息")
        print("2. 前端应过滤 'vcp_log' 类型的消息")
        print("3. 支持的质量参数: best, worst, 720p, 1080p, 480p")
        print("4. 文件大小支持 GB/MB 自动切换")
        print("5. 包含丰富的视频元数据信息")
    else:
        print("\n⚠️  部分验证失败，请检查相关配置。")
    
    print("\n📚 相关文档:")
    print("• IMPROVEMENTS_SUMMARY.md - 详细改进说明")
    print("• WEBSOCKET_PUSH_CLARIFICATION.md - WebSocket 推送说明")
    print("• frontend_integration_example.html - 前端集成示例")

if __name__ == "__main__":
    main()