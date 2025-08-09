#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的网络核心 - 解决403反爬虫问题
"""

import time
import random
import httpx
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

class EnhancedNetworkCore:
    """增强的网络核心，专门处理反爬虫"""
    
    def __init__(self):
        self.session = None
        self.last_request_time = 0
        self.min_delay = 2  # 最小延迟2秒
        self.max_delay = 5  # 最大延迟5秒
        
        # 多个User-Agent轮换
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # 多个Referer
        self.referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://missav.ws/',
            'https://www.missav.ws/',
            'https://missav.com/'
        ]
    
    def get_random_headers(self) -> Dict[str, str]:
        """获取随机化的请求头"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': random.choice(self.user_agents),
            'Referer': random.choice(self.referers)
        }
    
    def wait_between_requests(self):
        """请求间延迟"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_delay:
            delay = random.uniform(self.min_delay - elapsed, self.max_delay - elapsed)
            if delay > 0:
                print(f"⏱️ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def fetch_with_requests(self, url: str, max_retries: int = 3) -> Optional[str]:
        """使用requests库获取内容"""
        for attempt in range(max_retries):
            try:
                self.wait_between_requests()
                
                headers = self.get_random_headers()
                print(f"🔄 尝试 {attempt + 1}/{max_retries} - User-Agent: {headers['User-Agent'][:50]}...")
                
                # 使用session保持连接
                if not hasattr(self, 'requests_session'):
                    self.requests_session = requests.Session()
                
                response = self.requests_session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True,
                    verify=True
                )
                
                print(f"📊 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    content = response.text
                    print(f"✅ 成功获取内容，长度: {len(content)}")
                    return content
                elif response.status_code == 403:
                    print(f"❌ 403错误，尝试下一个策略...")
                    # 增加延迟
                    time.sleep(random.uniform(3, 8))
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 请求失败: {str(e)}")
                if attempt < max_retries - 1:
                    delay = random.uniform(5, 10)
                    print(f"⏱️ 等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
        
        return None
    
    def fetch_with_httpx(self, url: str, max_retries: int = 3) -> Optional[str]:
        """使用httpx库获取内容"""
        for attempt in range(max_retries):
            try:
                self.wait_between_requests()
                
                headers = self.get_random_headers()
                print(f"🔄 HTTPX尝试 {attempt + 1}/{max_retries}")
                
                with httpx.Client(
                    headers=headers,
                    timeout=30,
                    follow_redirects=True,
                    verify=True
                ) as client:
                    response = client.get(url)
                    
                    print(f"📊 状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        content = response.text
                        print(f"✅ 成功获取内容，长度: {len(content)}")
                        return content
                    elif response.status_code == 403:
                        print(f"❌ 403错误，尝试下一个策略...")
                        time.sleep(random.uniform(3, 8))
                    else:
                        print(f"❌ HTTP错误: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ HTTPX请求失败: {str(e)}")
                if attempt < max_retries - 1:
                    delay = random.uniform(5, 10)
                    print(f"⏱️ 等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
        
        return None
    
    def fetch_with_curl_simulation(self, url: str) -> Optional[str]:
        """模拟curl请求"""
        try:
            import subprocess
            import json
            
            headers = self.get_random_headers()
            
            # 构建curl命令
            curl_cmd = [
                'curl', '-s', '-L',  # silent, follow redirects
                '--max-time', '30',
                '--user-agent', headers['User-Agent'],
                '--referer', headers['Referer'],
                '-H', f"Accept: {headers['Accept']}",
                '-H', f"Accept-Language: {headers['Accept-Language']}",
                '-H', f"Accept-Encoding: {headers['Accept-Encoding']}",
                url
            ]
            
            print(f"🔧 尝试curl模拟请求...")
            
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                timeout=35
            )
            
            if result.returncode == 0 and result.stdout:
                content = result.stdout
                print(f"✅ curl成功获取内容，长度: {len(content)}")
                return content
            else:
                print(f"❌ curl失败: {result.stderr}")
                
        except Exception as e:
            print(f"❌ curl模拟失败: {str(e)}")
        
        return None
    
    def smart_fetch(self, url: str) -> Optional[str]:
        """智能获取 - 尝试多种方法"""
        print(f"🎯 智能获取: {url}")
        
        # 方法1: requests
        print("\n📡 方法1: 使用requests...")
        content = self.fetch_with_requests(url)
        if content:
            return content
        
        # 方法2: httpx
        print("\n🔗 方法2: 使用httpx...")
        content = self.fetch_with_httpx(url)
        if content:
            return content
        
        # 方法3: curl模拟
        print("\n🔧 方法3: 使用curl模拟...")
        content = self.fetch_with_curl_simulation(url)
        if content:
            return content
        
        print("\n❌ 所有方法都失败了")
        return None

def test_enhanced_network():
    """测试增强网络核心"""
    print("🚀 测试增强网络核心")
    print("=" * 60)
    
    core = EnhancedNetworkCore()
    test_url = "https://missav.ws/ofje-505"
    
    content = core.smart_fetch(test_url)
    
    if content:
        print(f"\n✅ 成功获取内容!")
        print(f"   长度: {len(content)}")
        
        # 检查关键内容
        if 'ofje-505' in content.lower():
            print("✅ 内容包含视频代码")
        else:
            print("⚠️ 内容不包含视频代码")
        
        # 保存到文件用于调试
        debug_file = Path("./debug_content.html")
        debug_file.write_text(content, encoding='utf-8')
        print(f"📁 内容已保存到: {debug_file}")
        
        return True
    else:
        print("\n❌ 获取内容失败")
        return False

if __name__ == "__main__":
    test_enhanced_network()