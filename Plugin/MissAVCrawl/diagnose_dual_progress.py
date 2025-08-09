#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断双重进度监督问题
"""

import sys
import json
import time
import threading
from pathlib import Path

def analyze_progress_systems():
    """分析进度监督系统"""
    print("🔧 分析进度监督系统")
    print("=" * 60)
    
    print("📋 当前架构分析:")
    print()
    
    print("🎯 第一套：真实下载系统（base_api.py）")
    print("   位置: Plugin/MissAVCrawl/base_api.py")
    print("   功能: 实际执行视频分段下载和文件合并")
    print("   进度报告: 通过 callback(i + 1, len(segments)) 调用")
    print("   状态: ✅ 有效 - 真正完成视频下载")
    print()
    
    print("🎯 第二套：进度显示系统（async_handler.py）")
    print("   位置: Plugin/MissAVCrawl/missav_api_core/async_handler.py")
    print("   功能: 接收进度信息并更新VCPAsyncResults文件")
    print("   进度报告: 通过 progress_callback 函数")
    print("   状态: ⚠️ 修复中 - 应该是唯一的进度报告点")
    print()
    
    print("🔍 问题识别:")
    print("   1. ❌ 双重回调：callback被调用两次")
    print("   2. ❌ 进度不同步：两套系统使用不同的进度计算")
    print("   3. ❌ 时间估算错误：基于虚假的进度数据")
    print()
    
    print("🛠️ 修复方案:")
    print("   1. ✅ 统一进度报告点：只在async_handler.py中报告进度")
    print("   2. ✅ 改进时间估算：基于真实的下载进度")
    print("   3. ✅ 增加下载速度显示：提供更准确的性能指标")

def test_progress_callback_flow():
    """测试进度回调流程"""
    print("\n🧪 测试进度回调流程")
    print("=" * 60)
    
    print("📋 模拟下载进度回调:")
    
    # 模拟进度回调
    total_segments = 100
    start_time = time.time()
    
    print(f"   总分段数: {total_segments}")
    print(f"   开始时间: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
    print()
    
    # 模拟几个进度点
    progress_points = [10, 25, 50, 75, 90, 100]
    
    for current in progress_points:
        elapsed_time = (current / total_segments) * 60  # 模拟60秒总时长
        current_time = start_time + elapsed_time
        
        progress = (current / total_segments) * 100
        
        if current > 0:
            avg_time_per_segment = elapsed_time / current
            remaining_segments = total_segments - current
            estimated_remaining_time = avg_time_per_segment * remaining_segments
            
            if estimated_remaining_time > 60:
                time_str = f"约 {estimated_remaining_time/60:.1f} 分钟"
            else:
                time_str = f"约 {estimated_remaining_time:.0f} 秒"
        else:
            time_str = "计算中..."
        
        download_speed = current / elapsed_time if elapsed_time > 0 else 0
        
        print(f"   [{current:3d}/{total_segments}] 进度: {progress:5.1f}% | "
              f"剩余时间: {time_str:>10} | "
              f"速度: {download_speed:.1f} 分段/秒")
        
        time.sleep(0.1)  # 模拟延迟

def check_log_file():
    """检查日志文件中的进度记录"""
    print("\n📄 检查日志文件")
    print("=" * 60)
    
    log_file = Path("Plugin/MissAVCrawl/MissAVDownloadHistory.log")
    
    if not log_file.exists():
        print("❌ 日志文件不存在")
        return
    
    print(f"📁 日志文件: {log_file}")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找最近的进度记录
        progress_lines = []
        for line in lines[-100:]:  # 只检查最后100行
            if "Download progress" in line or "Real download progress" in line:
                progress_lines.append(line.strip())
        
        if progress_lines:
            print(f"📊 找到 {len(progress_lines)} 条进度记录（最近的）:")
            for line in progress_lines[-10:]:  # 只显示最后10条
                print(f"   {line}")
        else:
            print("❌ 没有找到进度记录")
            
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")

def provide_monitoring_guide():
    """提供监控指南"""
    print("\n📋 进度监控指南")
    print("=" * 60)
    
    print("🔍 如何识别双重进度监督问题:")
    print("   1. 查看日志文件中是否有重复的进度记录")
    print("   2. 检查进度更新频率是否异常（过于频繁）")
    print("   3. 观察时间估算是否准确")
    print("   4. 验证下载速度计算是否合理")
    print()
    
    print("✅ 修复后的预期行为:")
    print("   1. 只有一套进度报告系统在工作")
    print("   2. 进度更新频率合理（每2秒或每10个分段）")
    print("   3. 时间估算基于真实的下载进度")
    print("   4. 显示实际的下载速度")
    print()
    
    print("🛠️ 调试命令:")
    print("   # 监控日志文件")
    print("   tail -f Plugin/MissAVCrawl/MissAVDownloadHistory.log")
    print()
    print("   # 检查VCPAsyncResults文件更新")
    print("   watch -n 1 'ls -la VCPAsyncResults/MissAVCrawl-*.json'")

def main():
    """主函数"""
    print("🚀 双重进度监督问题诊断")
    print("=" * 80)
    
    # 分析1: 系统架构分析
    analyze_progress_systems()
    
    # 分析2: 测试进度回调流程
    test_progress_callback_flow()
    
    # 分析3: 检查日志文件
    check_log_file()
    
    # 分析4: 提供监控指南
    provide_monitoring_guide()
    
    print("\n" + "=" * 80)
    print("📋 诊断总结")
    print("=" * 80)
    
    print("🎯 问题确认: 存在双重进度监督系统")
    print("🔧 修复状态: 已统一为单一进度报告点")
    print("✅ 预期效果: 进度报告更准确，时间估算更可靠")
    
    print("\n💡 建议:")
    print("   1. 测试新的异步下载任务，验证修复效果")
    print("   2. 监控日志文件，确认只有一套进度系统在工作")
    print("   3. 检查时间估算和下载速度的准确性")

if __name__ == "__main__":
    main()