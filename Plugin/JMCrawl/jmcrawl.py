#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JMCrawl VCP Plugin
基于 JMComic-Crawler-Python 的禁漫天堂漫画下载工具
"""

import sys
import json
import os
import traceback
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

# 尝试多种方式导入 jmcomic 模块
def import_jmcomic():
    """尝试导入 jmcomic 模块，支持多种安装方式"""
    import_errors = []
    
    # 方法1: 直接导入已安装的 jmcomic 包
    try:
        import jmcomic
        from jmcomic import JmOption, DirRule
        return jmcomic, JmOption, DirRule, "pip安装的jmcomic包"
    except ImportError as e:
        import_errors.append(f"pip包导入失败: {str(e)}")
    
    # 方法2: 从项目源码导入
    current_dir = Path(__file__).parent
    possible_paths = [
        # 相对于插件目录的可能路径
        current_dir.parent.parent.parent / "JMComic-Crawler-Python-master" / "src",
        current_dir.parent.parent.parent / "JMComic-Crawler-Python" / "src",
        current_dir.parent.parent / "JMComic-Crawler-Python-master" / "src",
        current_dir.parent.parent / "JMComic-Crawler-Python" / "src",
        current_dir.parent / "JMComic-Crawler-Python-master" / "src",
        current_dir.parent / "JMComic-Crawler-Python" / "src",
        current_dir / "JMComic-Crawler-Python-master" / "src",
        current_dir / "JMComic-Crawler-Python" / "src",
    ]
    
    for src_path in possible_paths:
        if src_path.exists():
            try:
                # 添加到 sys.path
                sys.path.insert(0, str(src_path))
                
                # 尝试导入
                import jmcomic
                from jmcomic import JmOption, DirRule
                
                return jmcomic, JmOption, DirRule, f"源码导入: {src_path}"
            except ImportError as e:
                import_errors.append(f"源码导入失败 ({src_path}): {str(e)}")
                # 从 sys.path 中移除
                if str(src_path) in sys.path:
                    sys.path.remove(str(src_path))
    
    # 方法3: 尝试安装缺失的依赖
    try:
        import subprocess
        print("尝试自动安装 jmcomic 依赖...", file=sys.stderr)
        
        # 安装 jmcomic
        result = subprocess.run([sys.executable, "-m", "pip", "install", "jmcomic"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            # 重新尝试导入
            import jmcomic
            from jmcomic import JmOption, DirRule
            return jmcomic, JmOption, DirRule, "自动安装后导入成功"
        else:
            import_errors.append(f"自动安装失败: {result.stderr}")
    except Exception as e:
        import_errors.append(f"自动安装异常: {str(e)}")
    
    # 所有方法都失败了
    error_msg = "无法导入 jmcomic 模块。尝试的方法:\n" + "\n".join(f"- {err}" for err in import_errors)
    error_msg += "\n\n解决方案:\n"
    error_msg += "1. 运行: pip install jmcomic\n"
    error_msg += "2. 或确保 JMComic-Crawler-Python 源码在正确位置\n"
    error_msg += "3. 或运行插件目录下的 install.py 脚本"
    
    raise ImportError(error_msg)

# 执行导入
try:
    jmcomic, JmOption, DirRule, import_method = import_jmcomic()
    print(f"JMComic 导入成功: {import_method}", file=sys.stderr)
    
    # 禁用 JMComic 的日志输出到 stdout，避免干扰 VCP 的 JSON 解析
    try:
        from jmcomic.jm_config import JmModuleConfig
        JmModuleConfig.disable_jm_log()
        print("已禁用 JMComic 日志输出", file=sys.stderr)
    except Exception as log_disable_error:
        print(f"禁用日志失败: {log_disable_error}", file=sys.stderr)
        
except ImportError as e:
    print(json.dumps({
        "status": "error",
        "error": str(e),
        "messageForAI": "JMComic 依赖库未正确安装或配置。请运行 'pip install jmcomic' 或检查源码路径。"
    }))
    sys.exit(1)


class OutputCapture:
    """捕获并重定向输出，确保只有 JSON 结果输出到 stdout"""
    def __init__(self):
        self.captured_stdout = StringIO()
        self.captured_stderr = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def __enter__(self):
        # 重定向 stdout 到我们的缓冲区
        sys.stdout = self.captured_stdout
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原始输出
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # 将捕获的内容输出到 stderr（调试用）
        captured_out = self.captured_stdout.getvalue()
        if captured_out.strip():
            print(f"[JMCrawl] 捕获的输出: {captured_out}", file=self.original_stderr)


class JMCrawlPlugin:
    def __init__(self):
        self.download_dir = os.getenv('JM_DOWNLOAD_DIR', './downloads/jm')
        self.client_impl = os.getenv('JM_CLIENT_IMPL', 'html')
        self.image_suffix = os.getenv('JM_IMAGE_SUFFIX', '.jpg')
        self.proxy = os.getenv('JM_PROXY', 'system')
        self.cookies = os.getenv('JM_COOKIES', '')
        
    def create_option(self, custom_dir=None, custom_format=None, force_api=False):
        """创建 JMComic 下载选项"""
        try:
            # 创建基础选项
            option = JmOption.default()
            
            # 设置下载目录
            download_dir = custom_dir or self.download_dir
            option.dir_rule = DirRule('Bd_Ptitle', base_dir=download_dir)
            
            # 设置客户端实现 - 如果遇到403错误，自动切换到API端
            if force_api:
                option.client.impl = 'api'
                print(f"客户端设置: 强制使用API端 (避免地区限制)", file=sys.stderr)
            else:
                option.client.impl = self.client_impl
                print(f"客户端设置: {self.client_impl}", file=sys.stderr)
            
            # 设置图片格式
            image_format = custom_format or self.image_suffix
            if image_format and not image_format.startswith('.'):
                image_format = '.' + image_format
            option.download.image.suffix = image_format
            
            # 关键修复：正确设置代理
            if self.proxy and self.proxy.lower() == 'null':
                # 明确禁用代理 - 这是关键！
                option.client.postman.meta_data.proxies = None
                print(f"代理设置: 已禁用代理", file=sys.stderr)
            elif self.proxy and self.proxy.lower() not in ['system', '']:
                # 处理具体的代理地址
                if ':' in self.proxy:
                    proxy_config = {
                        'http': self.proxy,
                        'https': self.proxy
                    }
                    option.client.postman.meta_data.proxies = proxy_config
                    print(f"代理设置: {proxy_config}", file=sys.stderr)
                else:
                    option.client.postman.meta_data.proxies = self.proxy
                    print(f"代理设置: {self.proxy}", file=sys.stderr)
            else:
                # 默认情况下也禁用代理，避免 system 代理解析问题
                option.client.postman.meta_data.proxies = None
                print(f"代理设置: 默认禁用代理 (避免system代理问题)", file=sys.stderr)
            
            # 设置 cookies
            if self.cookies:
                if '=' in self.cookies:
                    # 解析 cookies 字符串
                    cookies_dict = {}
                    for cookie in self.cookies.split(';'):
                        if '=' in cookie:
                            key, value = cookie.strip().split('=', 1)
                            cookies_dict[key] = value
                    option.client.postman.meta_data.cookies = cookies_dict
                    print(f"Cookies设置: {list(cookies_dict.keys())}", file=sys.stderr)
                else:
                    # 假设是 AVS cookie
                    option.client.postman.meta_data.cookies = {'AVS': self.cookies}
                    print(f"Cookies设置: AVS", file=sys.stderr)
            
            return option
        except Exception as e:
            raise Exception(f"创建下载选项失败: {str(e)}")
    
    def download_album(self, album_id, download_dir=None, image_format=None):
        """下载本子"""
        # 使用输出捕获确保不干扰 VCP 的 JSON 解析
        with OutputCapture():
            # 首先尝试默认设置
            try:
                option = self.create_option(download_dir, image_format)
                album, downloader = jmcomic.download_album(album_id, option)
                
                # 获取下载信息
                album_info = {
                    'id': album.album_id,
                    'name': album.name,
                    'author': getattr(album, 'author', '未知'),
                    'total_photos': len(album),  # 使用 len(album) 而不是 album.photo_list
                    'download_path': str(option.dir_rule.base_dir)
                }
                
                result_text = f"✅ 本子下载完成！\n"
                result_text += f"📖 本子名称: {album_info['name']}\n"
                result_text += f"🆔 本子ID: {album_info['id']}\n"
                result_text += f"👤 作者: {album_info['author']}\n"
                result_text += f"📚 章节数: {album_info['total_photos']}\n"
                result_text += f"📁 下载路径: {album_info['download_path']}"
                
                return {
                    "status": "success",
                    "result": result_text,
                    "messageForAI": f"成功下载本子 {album_id}，包含 {album_info['total_photos']} 个章节，保存在 {album_info['download_path']}"
                }
                
            except Exception as e:
                error_str = str(e)
                
                # 如果是403错误或地区限制，尝试切换到API端
                if "403" in error_str or "ip地区禁止访问" in error_str or "爬虫被识别" in error_str:
                    print(f"检测到地区限制，尝试切换到API端...", file=sys.stderr)
                    try:
                        option = self.create_option(download_dir, image_format, force_api=True)
                        album, downloader = jmcomic.download_album(album_id, option)
                        
                        # 获取下载信息
                        album_info = {
                            'id': album.album_id,
                            'name': album.name,
                            'author': getattr(album, 'author', '未知'),
                            'total_photos': len(album),  # 使用 len(album) 而不是 album.photo_list
                            'download_path': str(option.dir_rule.base_dir)
                        }
                        
                        result_text = f"✅ 本子下载完成！(已切换到API端)\n"
                        result_text += f"📖 本子名称: {album_info['name']}\n"
                        result_text += f"🆔 本子ID: {album_info['id']}\n"
                        result_text += f"👤 作者: {album_info['author']}\n"
                        result_text += f"📚 章节数: {album_info['total_photos']}\n"
                        result_text += f"📁 下载路径: {album_info['download_path']}"
                        
                        return {
                            "status": "success",
                            "result": result_text,
                            "messageForAI": f"成功下载本子 {album_id}（已自动切换到API端避免地区限制），包含 {album_info['total_photos']} 个章节"
                        }
                        
                    except Exception as e2:
                        error_msg = f"下载本子 {album_id} 失败: 网页端被限制({error_str})，API端也失败({str(e2)})"
                        return {
                            "status": "error",
                            "error": error_msg,
                            "messageForAI": f"下载本子 {album_id} 失败，可能需要配置代理或该地区无法访问。"
                        }
                
                # 其他错误
                error_msg = f"下载本子 {album_id} 失败: {error_str}"
                return {
                    "status": "error",
                    "error": error_msg,
                    "messageForAI": f"下载本子 {album_id} 时发生错误，请检查ID是否正确或网络连接。"
                }
    
    def download_photo(self, photo_id, download_dir=None, image_format=None):
        """下载章节"""
        # 使用输出捕获确保不干扰 VCP 的 JSON 解析
        with OutputCapture():
            try:
                option = self.create_option(download_dir, image_format)
                
                # 下载章节
                photo, downloader = jmcomic.download_photo(photo_id, option)
                
                # 获取下载信息
                photo_info = {
                    'id': photo.photo_id,
                    'name': photo.name,
                    'total_images': len(photo),  # 使用 len(photo) 而不是 photo.page_list
                    'download_path': str(option.dir_rule.base_dir)
                }
                
                result_text = f"✅ 章节下载完成！\n"
                result_text += f"📄 章节名称: {photo_info['name']}\n"
                result_text += f"🆔 章节ID: {photo_info['id']}\n"
                result_text += f"🖼️ 图片数: {photo_info['total_images']}\n"
                result_text += f"📁 下载路径: {photo_info['download_path']}"
                
                return {
                    "status": "success",
                    "result": result_text,
                    "messageForAI": f"成功下载章节 {photo_id}，包含 {photo_info['total_images']} 张图片，保存在 {photo_info['download_path']}"
                }
                
            except Exception as e:
                error_str = str(e)
                
                # 如果是403错误或地区限制，尝试切换到API端
                if "403" in error_str or "ip地区禁止访问" in error_str or "爬虫被识别" in error_str:
                    print(f"检测到地区限制，尝试切换到API端...", file=sys.stderr)
                    try:
                        option = self.create_option(download_dir, image_format, force_api=True)
                        photo, downloader = jmcomic.download_photo(photo_id, option)
                        
                        photo_info = {
                            'id': photo.photo_id,
                            'name': photo.name,
                            'total_images': len(photo),
                            'download_path': str(option.dir_rule.base_dir)
                        }
                        
                        result_text = f"✅ 章节下载完成！(已切换到API端)\n"
                        result_text += f"📄 章节名称: {photo_info['name']}\n"
                        result_text += f"🆔 章节ID: {photo_info['id']}\n"
                        result_text += f"🖼️ 图片数: {photo_info['total_images']}\n"
                        result_text += f"📁 下载路径: {photo_info['download_path']}"
                        
                        return {
                            "status": "success",
                            "result": result_text,
                            "messageForAI": f"成功下载章节 {photo_id}（已自动切换到API端避免地区限制），包含 {photo_info['total_images']} 张图片"
                        }
                        
                    except Exception as e2:
                        error_msg = f"下载章节 {photo_id} 失败: 网页端被限制({error_str})，API端也失败({str(e2)})"
                        return {
                            "status": "error",
                            "error": error_msg,
                            "messageForAI": f"下载章节 {photo_id} 失败，可能需要配置代理或该地区无法访问。"
                        }
                
                # 其他错误
                error_msg = f"下载章节 {photo_id} 失败: {error_str}"
                return {
                    "status": "error",
                    "error": error_msg,
                    "messageForAI": f"下载章节 {photo_id} 时发生错误，请检查ID是否正确或网络连接。"
                }
    
    def search_album(self, keyword, page=1, limit=10):
        """搜索本子"""
        # 使用输出捕获确保不干扰 VCP 的 JSON 解析
        with OutputCapture():
            try:
                option = self.create_option()
                client = option.new_jm_client()
                
                # 执行搜索 - 使用正确的搜索方法
                search_result = client.search_site(keyword, page=page)
                
                # 处理搜索结果
                albums = []
                count = 0
                
                print(f"搜索结果类型: {type(search_result)}", file=sys.stderr)
                print(f"搜索结果长度: {len(search_result) if hasattr(search_result, '__len__') else 'unknown'}", file=sys.stderr)
                
                # 检查搜索结果的结构
                for item in search_result:
                    if count >= limit:
                        break
                    
                    print(f"处理第 {count + 1} 个结果，类型: {type(item)}", file=sys.stderr)
                    
                    try:
                        # 尝试不同的结构解析方式
                        if isinstance(item, tuple) and len(item) == 2:
                            # 如果是元组 (album_id, album_info)
                            album_id, album_info = item
                            print(f"元组结构: ID={album_id}, Info类型={type(album_info)}", file=sys.stderr)
                            
                            if isinstance(album_info, dict):
                                # album_info 是字典
                                album_data = {
                                    'id': album_id,
                                    'name': album_info.get('name', album_info.get('title', '未知')),
                                    'author': album_info.get('author', '未知'),
                                    'tags': album_info.get('tags', []),
                                    'description': album_info.get('description', '')
                                }
                            else:
                                # album_info 不是字典，可能是字符串或其他类型
                                album_data = {
                                    'id': album_id,
                                    'name': str(album_info) if album_info else '未知',
                                    'author': '未知',
                                    'tags': [],
                                    'description': ''
                                }
                        elif hasattr(item, 'album_id') or hasattr(item, 'id'):
                            # 如果是对象，有 album_id 或 id 属性
                            album_data = {
                                'id': getattr(item, 'album_id', getattr(item, 'id', 'unknown')),
                                'name': getattr(item, 'name', getattr(item, 'title', '未知')),
                                'author': getattr(item, 'author', '未知'),
                                'tags': getattr(item, 'tags', []),
                                'description': getattr(item, 'description', '')
                            }
                        else:
                            # 其他情况，尝试转换为字符串
                            album_data = {
                                'id': str(count + 1),
                                'name': str(item)[:50] if item else '未知',
                                'author': '未知',
                                'tags': [],
                                'description': ''
                            }
                        
                        # 处理描述长度
                        if isinstance(album_data['description'], str) and len(album_data['description']) > 100:
                            album_data['description'] = album_data['description'][:100] + '...'
                        
                        albums.append(album_data)
                        count += 1
                        
                    except Exception as e:
                        print(f"处理搜索结果项失败: {str(e)}", file=sys.stderr)
                        print(f"结果项内容: {item}", file=sys.stderr)
                        # 创建一个基本的结果项
                        try:
                            album_data = {
                                'id': f'unknown_{count + 1}',
                                'name': f'解析失败的结果 {count + 1}',
                                'author': '未知',
                                'tags': [],
                                'description': f'原始数据: {str(item)[:50]}...'
                            }
                            albums.append(album_data)
                            count += 1
                        except:
                            continue
                
                if not albums:
                    result_text = f"🔍 搜索关键词 '{keyword}' 未找到相关结果"
                else:
                    result_text = f"🔍 搜索关键词 '{keyword}' 找到 {len(albums)} 个结果:\n\n"
                    for i, album in enumerate(albums, 1):
                        result_text += f"{i}. 📖 {album['name']}\n"
                        result_text += f"   🆔 ID: {album['id']}\n"
                        result_text += f"   👤 作者: {album['author']}\n"
                        if album['tags']:
                            result_text += f"   🏷️ 标签: {', '.join(album['tags'][:5])}\n"
                        if album['description']:
                            result_text += f"   📝 简介: {album['description']}\n"
                        result_text += "\n"
                
                return {
                    "status": "success",
                    "result": result_text,
                    "messageForAI": f"搜索关键词 '{keyword}' 完成，找到 {len(albums)} 个相关本子。"
                }
                
            except Exception as e:
                error_msg = f"搜索失败: {str(e)}"
                return {
                    "status": "error",
                    "error": error_msg,
                    "messageForAI": f"搜索关键词 '{keyword}' 时发生错误，请检查网络连接。"
                }
    
    def get_album_info(self, album_id):
        """获取本子信息"""
        # 使用输出捕获确保不干扰 VCP 的 JSON 解析
        with OutputCapture():
            # 首先尝试默认设置
            try:
                option = self.create_option()
                client = option.new_jm_client()
                album = client.get_album_detail(album_id)
                
                return self._format_album_info(album, album_id)
                
            except Exception as e:
                error_str = str(e)
                
                # 如果是403错误或地区限制，尝试切换到API端
                if "403" in error_str or "ip地区禁止访问" in error_str or "爬虫被识别" in error_str:
                    print(f"检测到地区限制，尝试切换到API端...", file=sys.stderr)
                    try:
                        option = self.create_option(force_api=True)
                        client = option.new_jm_client()
                        album = client.get_album_detail(album_id)
                        
                        result = self._format_album_info(album, album_id)
                        result["messageForAI"] += " (已自动切换到API端避免地区限制)"
                        return result
                        
                    except Exception as e2:
                        error_msg = f"获取本子信息失败: 网页端被限制({error_str})，API端也失败({str(e2)})"
                        return {
                            "status": "error",
                            "error": error_msg,
                            "messageForAI": f"获取本子 {album_id} 信息失败，可能需要配置代理或该地区无法访问。"
                        }
                
                # 其他错误
                error_msg = f"获取本子信息失败: {error_str}"
                return {
                    "status": "error",
                    "error": error_msg,
                    "messageForAI": f"获取本子 {album_id} 信息时发生错误，请检查ID是否正确。"
                }
    
    def _format_album_info(self, album, album_id):
        """格式化本子信息"""
        # 构建详细信息
        album_info = {
            'id': album.album_id,
            'name': album.name,
            'author': getattr(album, 'author', '未知'),
            'tags': getattr(album, 'tags', []),
            'description': getattr(album, 'description', ''),
            'total_photos': len(album),  # 使用 len(album)
            'photos': []
        }
        
        # 获取章节信息 - 使用索引访问而不是 photo_list
        max_photos_to_show = min(5, len(album))  # 最多显示5个章节
        for i in range(max_photos_to_show):
            try:
                photo = album[i]  # 使用索引访问
                photo_info = {
                    'id': photo.photo_id,
                    'name': photo.name,
                    'index': getattr(photo, 'index', i + 1)
                }
                album_info['photos'].append(photo_info)
            except Exception as e:
                print(f"获取章节 {i} 信息失败: {str(e)}", file=sys.stderr)
                break
        
        result_text = f"📖 本子详细信息:\n\n"
        result_text += f"🆔 ID: {album_info['id']}\n"
        result_text += f"📚 名称: {album_info['name']}\n"
        result_text += f"👤 作者: {album_info['author']}\n"
        result_text += f"📄 章节数: {album_info['total_photos']}\n"
        
        if album_info['tags']:
            result_text += f"🏷️ 标签: {', '.join(album_info['tags'])}\n"
        
        if album_info['description']:
            result_text += f"📝 简介: {album_info['description']}\n"
        
        if album_info['photos']:
            result_text += f"\n📚 章节列表 (前5个):\n"
            for photo in album_info['photos']:
                result_text += f"  {photo['index']}. {photo['name']} (ID: {photo['id']})\n"
        
        if album_info['total_photos'] > 5:
            result_text += f"  ... 还有 {album_info['total_photos'] - 5} 个章节\n"
        
        return {
            "status": "success",
            "result": result_text,
            "messageForAI": f"成功获取本子 {album_id} 的详细信息，包含 {album_info['total_photos']} 个章节。"
        }
    
    def process_request(self, request_data):
        """处理请求"""
        try:
            command = request_data.get('command', '').strip()
            
            if command == 'DownloadAlbum':
                album_id = request_data.get('album_id', '').strip()
                if not album_id:
                    return {
                        "status": "error",
                        "error": "缺少必需参数: album_id",
                        "messageForAI": "请提供要下载的本子ID。"
                    }
                
                download_dir = request_data.get('download_dir', '').strip() or None
                image_format = request_data.get('image_format', '').strip() or None
                
                return self.download_album(album_id, download_dir, image_format)
            
            elif command == 'DownloadPhoto':
                photo_id = request_data.get('photo_id', '').strip()
                if not photo_id:
                    return {
                        "status": "error",
                        "error": "缺少必需参数: photo_id",
                        "messageForAI": "请提供要下载的章节ID。"
                    }
                
                download_dir = request_data.get('download_dir', '').strip() or None
                image_format = request_data.get('image_format', '').strip() or None
                
                return self.download_photo(photo_id, download_dir, image_format)
            
            elif command == 'SearchAlbum':
                keyword = request_data.get('keyword', '').strip()
                if not keyword:
                    return {
                        "status": "error",
                        "error": "缺少必需参数: keyword",
                        "messageForAI": "请提供搜索关键词。"
                    }
                
                try:
                    page = int(request_data.get('page', 1))
                    limit = int(request_data.get('limit', 10))
                except ValueError:
                    page = 1
                    limit = 10
                
                return self.search_album(keyword, page, limit)
            
            elif command == 'GetAlbumInfo':
                album_id = request_data.get('album_id', '').strip()
                if not album_id:
                    return {
                        "status": "error",
                        "error": "缺少必需参数: album_id",
                        "messageForAI": "请提供要查询的本子ID。"
                    }
                
                return self.get_album_info(album_id)
            
            else:
                return {
                    "status": "error",
                    "error": f"未知命令: {command}",
                    "messageForAI": f"不支持的命令 '{command}'，请使用 DownloadAlbum、DownloadPhoto、SearchAlbum 或 GetAlbumInfo。"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"处理请求时发生错误: {str(e)}",
                "messageForAI": "处理请求时发生内部错误，请检查参数格式。"
            }


def main():
    try:
        # 确保所有非结果输出都重定向到 stderr
        print("JMCrawl 插件开始执行", file=sys.stderr)
        
        # 读取标准输入
        input_data = sys.stdin.read().strip()
        if not input_data:
            result = {
                "status": "error",
                "error": "未收到输入数据",
                "messageForAI": "插件未收到任何输入数据。"
            }
            print(json.dumps(result, ensure_ascii=False))
            return
        
        print(f"收到输入数据: {input_data[:100]}...", file=sys.stderr)
        
        # 解析 JSON 数据
        try:
            request_data = json.loads(input_data)
            print(f"JSON 解析成功: {request_data.get('command', 'unknown')}", file=sys.stderr)
        except json.JSONDecodeError as e:
            result = {
                "status": "error",
                "error": f"JSON 解析错误: {str(e)}",
                "messageForAI": "输入数据格式错误，请检查JSON格式。"
            }
            print(json.dumps(result, ensure_ascii=False))
            return
        
        # 创建插件实例并处理请求
        print("创建插件实例", file=sys.stderr)
        plugin = JMCrawlPlugin()
        
        print("开始处理请求", file=sys.stderr)
        result = plugin.process_request(request_data)
        
        print(f"请求处理完成: {result.get('status', 'unknown')}", file=sys.stderr)
        
        # 确保结果是有效的 JSON
        if not isinstance(result, dict):
            result = {
                "status": "error",
                "error": "插件返回了无效的结果格式",
                "messageForAI": "插件内部错误，返回格式不正确。"
            }
        
        # 输出结果到 stdout（这是 VCP 期望的）
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(f"插件执行异常: {str(e)}", file=sys.stderr)
        print(f"异常详情: {traceback.format_exc()}", file=sys.stderr)
        
        result = {
            "status": "error",
            "error": f"插件执行错误: {str(e)}",
            "messageForAI": "插件执行时发生未预期的错误。",
            "traceback": traceback.format_exc()
        }
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()