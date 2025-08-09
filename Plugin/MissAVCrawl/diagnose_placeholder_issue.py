#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断占位符问题的完整脚本
"""

import json
import re
import time
from pathlib import Path

def check_vcp_server_status():
    """检查VCP服务器状态"""
    print("🔧 检查VCP服务器状态")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get("http://localhost:6005", timeout=5)
        print(f"✅ VCP服务器响应: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ VCP服务器未运行或无法连接")
        return False
    except Exception as e:
        print(f"❌ 检查VCP服务器时出错: {str(e)}")
        return False

def create_test_scenario():
    """创建一个完整的测试场景"""
    print("\n🧪 创建测试场景")
    print("=" * 60)
    
    # 创建一个测试任务
    test_task_id = "diagnostic-test-12345"
    test_message = "✅ 诊断测试成功！\n\n这是一个用于诊断占位符问题的测试消息。\n如果你能看到这条消息，说明占位符替换功能正常工作。"
    
    # 创建测试结果文件
    result_data = {
        "requestId": test_task_id,
        "status": "Succeed",
        "pluginName": "MissAVCrawl",
        "message": test_message,
        "timestamp": "2025-08-03T02:00:00.000000"
    }
    
    result_file = Path(f"VCPAsyncResults/MissAVCrawl-{test_task_id}.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 创建测试结果文件: {result_file}")
    
    # 生成对应的占位符
    placeholder = f"{{{{VCP_ASYNC_RESULT::MissAVCrawl::{test_task_id}}}}}"
    
    print(f"🎯 测试占位符: {placeholder}")
    print(f"📝 期望替换结果: {test_message}")
    
    return test_task_id, placeholder, test_message

def test_placeholder_in_context():
    """测试占位符在上下文中的表现"""
    print("\n🔍 测试占位符在上下文中的表现")
    print("=" * 60)
    
    test_task_id, placeholder, expected_message = create_test_scenario()
    
    # 模拟AI对话上下文
    conversation_context = f"""
用户: 请帮我下载一个视频

AI: 好的，我已经为您提交了视频下载任务。

{placeholder}

任务正在后台处理中，请稍等。

用户: 现在状态如何？

AI: 让我检查一下任务状态。

{placeholder}

这是最新的任务状态。
"""
    
    print("📄 模拟对话上下文:")
    print(conversation_context)
    
    # 执行占位符替换
    print("\n🔄 执行占位符替换...")
    
    # 使用正则表达式查找和替换
    regex = r'\{\{VCP_ASYNC_RESULT::([a-zA-Z0-9_.-]+)::([a-zA-Z0-9_-]+)\}\}'
    
    def replace_placeholder(match):
        plugin_name = match.group(1)
        request_id = match.group(2)
        
        result_file_path = Path(f"VCPAsyncResults/{plugin_name}-{request_id}.json")
        
        if result_file_path.exists():
            try:
                with open(result_file_path, 'r', encoding='utf-8') as f:
                    callback_data = json.load(f)
                
                if 'message' in callback_data and callback_data['message']:
                    return callback_data['message']
                else:
                    return f"[任务 {plugin_name} (ID: {request_id}) 已完成]"
            except Exception:
                return f"[获取任务 {plugin_name} (ID: {request_id}) 结果时出错]"
        else:
            return f"[任务 {plugin_name} (ID: {request_id}) 结果待更新...]"
    
    processed_context = re.sub(regex, replace_placeholder, conversation_context)
    
    print("📤 处理后的上下文:")
    print(processed_context)
    
    # 检查是否正确替换
    if expected_message in processed_context:
        print("✅ 占位符替换成功！")
        return True
    else:
        print("❌ 占位符替换失败！")
        return False

def provide_troubleshooting_guide():
    """提供故障排除指南"""
    print("\n🛠️ 故障排除指南")
    print("=" * 60)
    
    print("如果占位符仍然不工作，请按以下步骤检查：")
    print()
    print("1. 📋 检查AI生成的占位符格式")
    print("   - 确保格式完全匹配: {{VCP_ASYNC_RESULT::MissAVCrawl::TaskID}}")
    print("   - 检查是否有多余的空格或特殊字符")
    print("   - 确保TaskID完全匹配文件名中的ID")
    print()
    print("2. 🕐 检查时机问题")
    print("   - 确保在任务提交后等待足够时间")
    print("   - 检查任务是否已经完成（查看VCPAsyncResults文件）")
    print()
    print("3. 🔧 检查VCP服务器配置")
    print("   - 确保VCP服务器正在运行")
    print("   - 检查server.js中的replaceCommonVariables函数")
    print("   - 确保VCP_ASYNC_RESULTS_DIR路径正确")
    print()
    print("4. 📁 检查文件权限")
    print("   - 确保VCPAsyncResults目录可读")
    print("   - 确保结果文件格式正确（有效的JSON）")
    print()
    print("5. 🐛 启用调试模式")
    print("   - 在config.env中设置DebugMode=true")
    print("   - 查看VCP服务器控制台输出")
    print("   - 检查是否有错误日志")

def main():
    """主诊断函数"""
    print("🚀 VCP占位符问题完整诊断")
    print("=" * 80)
    
    # 检查1: VCP服务器状态
    server_ok = check_vcp_server_status()
    
    # 检查2: 占位符替换测试
    placeholder_ok = test_placeholder_in_context()
    
    print("\n" + "=" * 80)
    print("📋 诊断结果")
    print("=" * 80)
    
    print(f"VCP服务器状态: {'✅ 正常' if server_ok else '❌ 异常'}")
    print(f"占位符替换测试: {'✅ 通过' if placeholder_ok else '❌ 失败'}")
    
    if server_ok and placeholder_ok:
        print("\n🎉 所有诊断测试通过！")
        print("占位符替换功能应该正常工作。")
        print("\n💡 如果问题仍然存在，可能是以下原因：")
        print("   - AI没有正确包含占位符")
        print("   - 占位符格式有细微错误")
        print("   - VCP服务器的replaceCommonVariables函数没有被调用")
    else:
        print("\n❌ 发现问题！")
        provide_troubleshooting_guide()

if __name__ == "__main__":
    main()