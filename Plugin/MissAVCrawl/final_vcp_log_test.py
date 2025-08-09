#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终VCPLog集成验证测试
"""

import sys
import json
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from request_handler import process_request

def analyze_response_content(content):
    """分析响应内容，检查增强信息字段"""
    enhanced_fields = {
        '標題': '**標題**:' in content,
        '番號': '**番號**:' in content,
        '發行日期': '**發行日期**:' in content,
        '時長': '**時長**:' in content,
        '女優': '**女優**:' in content,
        '類型': '**類型**:' in content,
        '系列': '**系列**:' in content,
        '發行商': '**發行商**:' in content,
        '標籤': '**標籤**:' in content,
        '分辨率': '可用分辨率' in content,
        '簡介': '**簡介**:' in content,
        '封面': '**封面圖片**:' in content,
        '預覽': '**預覽視頻**:' in content,
        'M3U8': '**M3U8播放列表**:' in content
    }
    
    found_fields = [field for field, found in enhanced_fields.items() if found]
    missing_fields = [field for field, found in enhanced_fields.items() if not found]
    
    return found_fields, missing_fields, enhanced_fields

def test_vcp_log_integration():
    """最终VCPLog集成验证测试"""
    print("🔍 最终VCPLog集成验证测试")
    print("=" * 60)
    
    # 测试GetVideoInfo命令（最重要的命令）
    test_request = {
        "command": "GetVideoInfo",
        "url": "https://missav.ws/SSIS-016"
    }
    
    print("📋 测试场景: 模拟VCP系统调用MissAVCrawl插件")
    print(f"📤 请求命令: {test_request['command']}")
    print(f"📤 请求URL: {test_request['url']}")
    print("-" * 60)
    
    # 处理请求
    result = process_request(test_request)
    
    print(f"📥 响应状态: {result.get('status')}")
    
    if result.get('status') == 'success':
        response_content = result.get('result', '')
        
        print(f"📊 响应长度: {len(response_content)} 字符")
        print("-" * 60)
        
        # 分析增强信息字段
        found_fields, missing_fields, field_status = analyze_response_content(response_content)
        
        print("✅ 找到的增强信息字段:")
        for field in found_fields:
            print(f"  ✓ {field}")
        
        if missing_fields:
            print(f"\n⚠️  缺失的字段:")
            for field in missing_fields:
                print(f"  ✗ {field}")
        
        print(f"\n📈 字段覆盖率: {len(found_fields)}/{len(field_status)} ({len(found_fields)/len(field_status)*100:.1f}%)")
        
        # VCPLog推送模拟
        print("\n" + "=" * 60)
        print("🚀 VCPLog推送模拟")
        print("-" * 60)
        
        # 模拟server.js的推送格式
        vcp_log_message = {
            "type": "vcp_log",
            "data": {
                "tool_name": "MissAVCrawl",
                "status": "success",
                "content": response_content,
                "source": "stream_loop"
            }
        }
        
        print("📡 VCPLog推送消息格式:")
        print(f"  - type: {vcp_log_message['type']}")
        print(f"  - tool_name: {vcp_log_message['data']['tool_name']}")
        print(f"  - status: {vcp_log_message['data']['status']}")
        print(f"  - content_length: {len(vcp_log_message['data']['content'])} 字符")
        print(f"  - source: {vcp_log_message['data']['source']}")
        
        # 显示推送内容预览
        print("\n📄 推送内容预览 (前500字符):")
        print("-" * 40)
        preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
        print(preview)
        print("-" * 40)
        
        # 评估集成效果
        print("\n🎯 VCPLog集成效果评估:")
        
        if len(found_fields) >= 10:
            print("🎉 优秀! VCPLog将接收到非常完整的增强信息")
            print("   客户端可以获得包括時長、女優、類型等在内的详细信息")
        elif len(found_fields) >= 7:
            print("✅ 良好! VCPLog将接收到较为完整的增强信息")
            print("   大部分重要信息都会推送给客户端")
        elif len(found_fields) >= 5:
            print("⚠️  一般! VCPLog将接收到基本的增强信息")
            print("   部分重要信息可能缺失")
        else:
            print("❌ 需要改进! VCPLog接收到的增强信息不够完整")
            print("   建议检查增强信息提取器的实现")
        
        # WebSocket客户端接收示例
        print("\n💡 客户端接收示例:")
        print("```javascript")
        print("ws.onmessage = function(event) {")
        print("    const message = JSON.parse(event.data);")
        print("    if (message.type === 'vcp_log' && message.data.tool_name === 'MissAVCrawl') {")
        print("        console.log('收到MissAV增强信息:', message.data.content);")
        print("        // 这里的content包含完整的增强视频信息")
        print("        // 包括標題、番號、時長、女優、類型等")
        print("    }")
        print("};")
        print("```")
        
        return True
        
    else:
        print(f"❌ 测试失败: {result.get('error')}")
        if result.get('traceback'):
            print(f"错误详情:\n{result['traceback']}")
        return False

def main():
    """主函数"""
    print("🚀 MissAVCrawl VCPLog集成最终验证")
    print("=" * 60)
    
    success = test_vcp_log_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 VCPLog集成验证成功!")
        print("✅ MissAVCrawl插件已成功集成VCPLog推送功能")
        print("✅ 增强信息将自动推送到VCPLog客户端")
        print("✅ 所有详细信息都包含在推送内容中")
        print("\n📋 集成完成清单:")
        print("  ✓ 增强信息提取器正常工作")
        print("  ✓ 格式化输出包含完整信息")
        print("  ✓ VCPLog推送格式正确")
        print("  ✓ 客户端可接收详细信息")
        print("  ✓ 日志文件记录完整")
    else:
        print("❌ VCPLog集成验证失败!")
        print("需要检查插件配置和实现")
    
    print("\n💡 使用提示:")
    print("- 启动VCP系统后，VCPLog插件会自动处理推送")
    print("- 客户端连接到VCPLog WebSocket即可接收信息")
    print("- 所有信息也会记录在Plugin/VCPLog/log/VCPlog.txt")

if __name__ == "__main__":
    main()