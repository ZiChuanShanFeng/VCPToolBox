#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证MissAVCrawl插件配置和环境
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_config():
    """验证插件配置"""
    print("🔧 验证MissAVCrawl插件配置")
    print("=" * 60)
    
    # 加载配置
    config_path = Path(__file__).parent / 'config.env'
    if not config_path.exists():
        print("❌ config.env文件不存在")
        return False
    
    load_dotenv(dotenv_path=config_path)
    
    # 检查必要的配置项
    required_configs = {
        'MISSAV_DOWNLOAD_DIR': os.getenv('MISSAV_DOWNLOAD_DIR', './downloads'),
        'MISSAV_QUALITY': os.getenv('MISSAV_QUALITY', 'best'),
        'MISSAV_DOWNLOADER': os.getenv('MISSAV_DOWNLOADER', 'threaded'),
        'CALLBACK_BASE_URL': os.getenv('CALLBACK_BASE_URL')
    }
    
    print("📋 配置项检查:")
    all_good = True
    
    for key, value in required_configs.items():
        if value:
            print(f"   ✅ {key}: {value}")
        else:
            print(f"   ❌ {key}: 未配置")
            if key == 'CALLBACK_BASE_URL':
                all_good = False
    
    # 检查下载目录
    download_dir = Path(required_configs['MISSAV_DOWNLOAD_DIR'])
    try:
        download_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 下载目录可写: {download_dir}")
    except Exception as e:
        print(f"   ❌ 下载目录创建失败: {e}")
        all_good = False
    
    # 检查VCPAsyncResults目录
    async_results_dir = Path("../../VCPAsyncResults")
    try:
        async_results_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 异步结果目录可写: {async_results_dir}")
    except Exception as e:
        print(f"   ❌ 异步结果目录创建失败: {e}")
        all_good = False
    
    # 检查依赖模块
    print("\n📦 依赖模块检查:")
    required_modules = [
        'requests',
        'pathlib',
        'json',
        'uuid',
        'threading',
        'dotenv'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module}: 未安装")
            all_good = False
    
    # 检查插件核心模块
    print("\n🔌 插件模块检查:")
    plugin_modules = [
        'base_api',
        'missav_api_core.async_handler',
        'missav_api_core.missav_api'
    ]
    
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    for module in plugin_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("✅ 所有配置和依赖检查通过！")
        print("插件应该可以正常工作。")
    else:
        print("❌ 发现配置或依赖问题！")
        print("请根据上述检查结果修复问题。")
    
    return all_good

if __name__ == "__main__":
    validate_config()