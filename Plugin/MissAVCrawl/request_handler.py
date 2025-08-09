#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 请求处理器 - 使用模块化结构
"""

import sys
import json
import traceback
from pathlib import Path

# 确保可以导入项目内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入模块化组件
from missav_api_core import MissAVCrawler


def process_request(request_data: dict) -> dict:
    """处理请求"""
    try:
        command = request_data.get('command', '').strip()
        
        if not command:
            return {
                "status": "error",
                "error": "缺少 command 参数"
            }
        
        # 初始化爬虫
        crawler = MissAVCrawler()
        
        if command == "GetVideoInfo":
            url = request_data.get('url', '') or ''
            if isinstance(url, str):
                url = url.strip()
            else:
                url = str(url).strip() if url is not None else ''
            if not url:
                return {
                    "status": "error",
                    "error": "缺少 url 参数"
                }
            
            # 使用增强信息提取功能（优先实时查找，失败时使用缓存）
            if hasattr(crawler, 'client') and hasattr(crawler.client, 'get_enhanced_video_info'):
                result = crawler.client.get_enhanced_video_info(url, use_cache=True)
                
                if result.get("success"):
                    # 使用增强格式化器
                    if hasattr(crawler.client.info_extractor, 'format_info_response'):
                        response_text = crawler.client.info_extractor.format_info_response(result)
                    else:
                        # 回退到基础格式化
                        info = result.get("info", result)
                        response_text = f"""### MissAV 增强视频信息 ###

**標題**: {info.get('title', '未知')}
**番號**: {info.get('video_code', '未知')}
**發行日期**: {info.get('release_date', info.get('publish_date', '未知'))}
**時長**: {info.get('duration', '未知')}
**女優**: {', '.join(info.get('actresses', []))}
**類型**: {', '.join(info.get('types', []))}
**系列**: {info.get('series', '未知')}
**發行商**: {info.get('publisher', '未知')}
**標籤**: {', '.join(info.get('tags', []))}
**封面圖片**: {info.get('main_cover', info.get('thumbnail', '未知'))}
**M3U8播放列表**: {info.get('m3u8_url', '未知')}
**原始URL**: {url}

增强视频信息获取成功！"""
                    
                    return {
                        "status": "success",
                        "result": response_text
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("error", "获取增强视频信息失败")
                    }
            else:
                # 回退到基础信息获取
                result = crawler.get_video_info(url)
                
                if result["success"]:
                    info = result["info"]
                    response_text = f"""### MissAV 基础视频信息 ###

**标题**: {info['title']}
**视频代码**: {info['video_code']}
**发布日期**: {info['publish_date']}
**缩略图**: {info['thumbnail']}
**M3U8 URL**: {info['m3u8_url']}
**原始URL**: {info['url']}

基础视频信息获取成功！"""
                    
                    return {
                        "status": "success",
                        "result": response_text
                    }
                else:
                    return {
                        "status": "error",
                        "error": result["error"]
                    }
        
        elif command == "DownloadVideo":
            url = request_data.get('url', '') or ''
            if isinstance(url, str):
                url = url.strip()
            else:
                url = str(url).strip() if url is not None else ''
            if not url:
                return {
                    "status": "error",
                    "error": "缺少 url 参数"
                }
            
            quality = request_data.get('quality', '').strip()
            download_dir = request_data.get('download_dir', '').strip()
            downloader = request_data.get('downloader', '').strip()
            
            result = crawler.download_video(
                url=url,
                quality=quality if quality else None,
                download_dir=download_dir if download_dir else None,
                downloader=downloader if downloader else None
            )
            
            if result["success"]:
                info = result["video_info"]
                response_text = f"""### MissAV 视频下载完成 ###

标题: {info['title']}
视频代码: {info['video_code']}
发布日期: {info['publish_date']}
文件路径: {result['file_path']}
下载目录: {result['download_dir']}
视频质量: {result['quality']}

视频下载成功！文件已保存到指定目录。"""
                
                return {
                    "status": "success",
                    "result": response_text
                }
            else:
                error_msg = result.get("error", "未知错误")
                if "video_info" in result:
                    info = result["video_info"]
                    error_msg += f"\n视频信息: {info['title']} ({info['video_code']})"
                
                return {
                    "status": "error",
                    "error": error_msg
                }
        
        elif command == "SearchVideos":
            keyword = request_data.get('keyword', '') or ''
            if isinstance(keyword, str):
                keyword = keyword.strip()
            else:
                keyword = str(keyword).strip() if keyword is not None else ''
            if not keyword:
                return {
                    "status": "error",
                    "error": "缺少 keyword 参数"
                }
            
            # 处理页码参数
            page = request_data.get('page', 1)
            try:
                page = int(page) if page else 1
                if page < 1:
                    page = 1
            except (ValueError, TypeError):
                page = 1
            
            # 处理排序参数
            sort = request_data.get('sort', '').strip()
            valid_sorts = ['saved', 'today_views', 'weekly_views', 'monthly_views', 'views', 'updated', 'released_at']
            if sort and sort not in valid_sorts:
                sort = None
            
            # 处理过滤器参数
            filter_type = request_data.get('filter', '').strip()
            valid_filters = ['all', 'single', 'japanese', 'uncensored_leak', 'uncensored', 'chinese_subtitle']
            if filter_type and filter_type not in valid_filters:
                filter_type = None
            
            # 处理封面图片参数
            include_cover = request_data.get('include_cover', True)
            if isinstance(include_cover, str):
                include_cover = include_cover.lower() in ['true', '1', 'yes', 'on']
            
            # 处理标题参数
            include_title = request_data.get('include_title', True)
            if isinstance(include_title, str):
                include_title = include_title.lower() in ['true', '1', 'yes', 'on']
            
            # 处理最大结果数参数
            max_results = request_data.get('max_results', 20)
            try:
                max_results = int(max_results) if max_results else 20
                if max_results < 1:
                    max_results = 20
                elif max_results > 100:
                    max_results = 100
            except (ValueError, TypeError):
                max_results = 20
            
            # 处理最大页数参数
            max_pages = request_data.get('max_pages', 1)
            try:
                max_pages = int(max_pages) if max_pages else 1
                if max_pages < 1:
                    max_pages = 1
                elif max_pages > 10:
                    max_pages = 10
            except (ValueError, TypeError):
                max_pages = 1
            
            # 处理增强信息参数
            enhanced_info = request_data.get('enhanced_info', False)
            if isinstance(enhanced_info, str):
                enhanced_info = enhanced_info.lower() in ['true', '1', 'yes', 'on']
            
            # 使用增强搜索功能
            if hasattr(crawler, 'client') and hasattr(crawler.client, 'search_videos_with_filters'):
                result = crawler.client.search_videos_with_filters(
                    keyword=keyword, 
                    page=page, 
                    sort=sort,
                    filter_type=filter_type,
                    include_cover=include_cover,
                    include_title=include_title,
                    max_results=max_results,
                    max_pages=max_pages,
                    enhanced_info=enhanced_info
                )
            else:
                # 回退到原有搜索功能
                result = crawler.search_videos(
                    keyword=keyword, 
                    page=page, 
                    sort=sort,
                    include_cover=include_cover,
                    include_title=include_title,
                    max_results=max_results,
                    max_pages=max_pages
                )
            
            if result["success"]:
                results = result["results"]
                
                # 构建排序说明
                sort_desc = ""
                if sort:
                    sort_names = {
                        'saved': '收藏数',
                        'today_views': '日流量',
                        'weekly_views': '周流量',
                        'monthly_views': '月流量',
                        'views': '总流量',
                        'updated': '最近更新',
                        'released_at': '发行日期'
                    }
                    sort_desc = f"排序方式: {sort_names.get(sort, sort)}\n"
                
                response_text = f"""### MissAV 增强搜索结果 ###

搜索关键词: {keyword}
页码范围: {page} - {page + max_pages - 1}
{sort_desc}找到视频数量: {result['total_count']}
实际页数: {result.get('actual_pages', 1)}

"""
                
                if results:
                    response_text += "搜索结果:\n\n"
                    
                    for i, video in enumerate(results, 1):
                        response_text += f"{i}. **{video['title']}**\n"
                        response_text += f"   视频代码: {video['video_code']}\n"
                        response_text += f"   链接: {video['url']}\n"
                        
                        if include_cover and video.get('thumbnail'):
                            response_text += f"   封面图片: {video['thumbnail']}\n"
                        
                        if include_title and video.get('full_title') and video.get('full_title') != video.get('title'):
                            response_text += f"   完整标题: {video['full_title']}\n"
                        
                        if video.get('publish_date'):
                            response_text += f"   发布日期: {video['publish_date']}\n"
                        
                        if video.get('views'):
                            response_text += f"   观看次数: {video['views']}\n"
                        
                        response_text += "\n"

                else:
                    response_text += "未找到相关视频。\n"
                
                response_text += "\n搜索完成！"
                
                return {
                    "status": "success",
                    "result": response_text
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "搜索失败")
                }
        
        elif command == "GetHotVideos":
            category = request_data.get('category', 'daily') or 'daily'
            if isinstance(category, str):
                category = category.strip().lower()
            else:
                category = str(category).strip().lower() if category is not None else 'daily'
            
            # 扩展有效分类参数，包括新的真实热榜分类
            valid_categories = [
                'daily', 'weekly', 'monthly', 'new', 'popular', 'trending',
                'chinese_subtitle', 'uncensored_leak', 'siro', 'luxu', 'gana'
            ]
            if category not in valid_categories:
                category = 'daily'
            
            page = request_data.get('page', 1)
            try:
                page = int(page) if page else 1
                if page < 1:
                    page = 1
            except (ValueError, TypeError):
                page = 1
            
            # 处理排序参数
            sort = request_data.get('sort', '').strip()
            valid_sorts = ['saved', 'today_views', 'weekly_views', 'monthly_views', 'views', 'updated', 'released_at']
            if sort and sort not in valid_sorts:
                sort = None
            
            # 处理过滤器参数
            filter_type = request_data.get('filter', '').strip()
            valid_filters = ['all', 'single', 'japanese', 'uncensored_leak', 'uncensored', 'chinese_subtitle']
            if filter_type and filter_type not in valid_filters:
                filter_type = None
            
            # 优先使用新的真实热榜功能
            result = None
            
            # 如果crawler可用且有新的热榜功能，使用它
            if crawler and hasattr(crawler, 'client') and hasattr(crawler.client, 'get_hot_videos_with_filters'):
                try:
                    result = crawler.client.get_hot_videos_with_filters(category, page, sort, filter_type)
                except Exception as e:
                    print(f"新热榜功能失败: {str(e)}")
                    result = None
            
            # 如果新功能不可用，尝试直接使用EnhancedHotVideos
            if result is None:
                try:
                    from missav_api_core.enhanced_hot_videos import EnhancedHotVideos
                    enhanced_hot = EnhancedHotVideos()
                    result = enhanced_hot.get_hot_videos_with_filters(category, page, sort, filter_type)
                except Exception as e:
                    print(f"直接使用EnhancedHotVideos失败: {str(e)}")
                    result = None
            
            # 如果所有新功能都不可用，使用旧的热榜功能作为最后备用
            # 不再使用虚构数据作为备用源，直接返回真实结果
            if result is None or not result.get("success"):
                return {
                    "status": "error",
                    "result": f"获取热榜失败: 无法从真实数据源获取 {category} 热榜数据"
                }
            
            if result and result.get("success"):
                results = result["results"]
                category_name = {
                    'daily': '每日热门',
                    'weekly': '每周热门', 
                    'monthly': '每月热门',
                    'new': '最新视频',
                    'popular': '最受欢迎',
                    'trending': '趋势视频',
                    'chinese_subtitle': '中文字幕',
                    'uncensored_leak': '无码流出',
                    'siro': 'SIRO系列',
                    'luxu': 'LUXU系列',
                    'gana': 'GANA系列'
                }.get(category, '热门视频')
                
                response_text = f"""### MissAV {category_name} ###

分类: {category_name}
页码: {page}"""
                
                # 添加数据源信息
                if result.get("source"):
                    source_names = {
                        "real_crawl": "真实爬取",
                        "fallback_with_filters": "备用数据源",
                        "generated_data": "模拟数据"
                    }
                    source_name = source_names.get(result["source"], result["source"])
                    response_text += f"\n数据源: {source_name}"
                
                # 添加排序和过滤器信息
                if result.get("applied_sort") or sort:
                    sort_names = {
                        'saved': '收藏数',
                        'today_views': '日流量',
                        'weekly_views': '周流量',
                        'monthly_views': '月流量',
                        'views': '总流量',
                        'updated': '最近更新',
                        'released_at': '发行日期'
                    }
                    applied_sort = result.get("applied_sort") or sort
                    response_text += f"\n排序方式: {sort_names.get(applied_sort, applied_sort)}"
                
                if result.get("applied_filter") or filter_type:
                    filter_names = {
                        'all': '所有',
                        'single': '單人作品',
                        'japanese': '日本AV',
                        'uncensored_leak': '無碼流出',
                        'uncensored': '無碼影片',
                        'chinese_subtitle': '中文字幕'
                    }
                    applied_filter = result.get("applied_filter") or filter_type
                    response_text += f"\n过滤器: {filter_names.get(applied_filter, applied_filter)}"
                
                response_text += f"\n视频数量: {result['total_count']}\n\n"
                
                if results:
                    response_text += "热榜视频:\n\n"
                    for i, video in enumerate(results, 1):
                        response_text += f"{i}. **{video['title']}**\n"
                        response_text += f"   视频代码: {video['video_code']}\n"
                        response_text += f"   链接: {video['url']}\n"
                        if video.get('thumbnail'):
                            response_text += f"   缩略图: {video['thumbnail']}\n"
                        if video.get('duration'):
                            response_text += f"   时长: {video['duration']}\n"
                        if video.get('publish_date'):
                            response_text += f"   发布日期: {video['publish_date']}\n"
                        response_text += "\n"

                else:
                    response_text += "暂无热榜视频。\n"
                
                # 添加提示信息
                if result.get("note"):
                    response_text += f"\n💡 {result['note']}\n"
                elif result.get("source") == "real_crawl":
                    response_text += f"\n✅ 数据来源于真实网站爬取\n"
                
                response_text += "\n热榜获取完成！"
                
                return {
                    "status": "success",
                    "result": response_text
                }
            else:
                error_msg = result.get("error", "获取热榜失败") if result else "热榜功能不可用"
                return {
                    "status": "error",
                    "error": error_msg
                }
        
        elif command == "GetEnhancedVideoInfo":
            url = request_data.get('url', '') or ''
            if isinstance(url, str):
                url = url.strip()
            else:
                url = str(url).strip() if url is not None else ''
            if not url:
                return {
                    "status": "error",
                    "error": "缺少 url 参数"
                }
            
            use_cache = request_data.get('use_cache', True)
            if isinstance(use_cache, str):
                use_cache = use_cache.lower() in ['true', '1', 'yes', 'on']
            
            # 使用增强信息提取功能
            if hasattr(crawler, 'client') and hasattr(crawler.client, 'get_enhanced_video_info'):
                result = crawler.client.get_enhanced_video_info(url, use_cache)
            else:
                # 回退到基础信息获取
                result = crawler.get_video_info(url)
            
            if result.get("success"):
                # 使用增强格式化器
                if hasattr(crawler, 'client') and hasattr(crawler.client.info_extractor, 'format_info_response'):
                    response_text = crawler.client.info_extractor.format_info_response(result)
                else:
                    # 基础格式化
                    info = result.get("info", result)
                    response_text = f"""### MissAV 增强视频信息 ###

**标题**: {info.get('title', '未知')}
**视频代码**: {info.get('video_code', '未知')}
**发布日期**: {info.get('publish_date', '未知')}
**时长**: {info.get('duration', '未知')}
**缩略图**: {info.get('thumbnail', info.get('main_cover', '未知'))}
**原始URL**: {url}

增强信息获取成功！"""
                
                return {
                    "status": "success",
                    "result": response_text
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "获取增强视频信息失败")
                }
        
        elif command == "GetPreviewVideos":
            url = request_data.get('url', '') or ''
            if isinstance(url, str):
                url = url.strip()
            else:
                url = str(url).strip() if url is not None else ''
            if not url:
                return {
                    "status": "error",
                    "error": "缺少 url 参数"
                }
            
            download = request_data.get('download', False)
            if isinstance(download, str):
                download = download.lower() in ['true', '1', 'yes', 'on']
            
            video_code = request_data.get('video_code', '').strip()
            output_dir = request_data.get('output_dir', '').strip()
            
            # 使用预览视频功能
            if hasattr(crawler, 'client') and hasattr(crawler.client, 'get_preview_videos'):
                result = crawler.client.get_preview_videos(
                    url, 
                    download=download, 
                    video_code=video_code if video_code else None,
                    output_dir=output_dir if output_dir else None
                )
                
                if result.get("success"):
                    # 使用预览下载器的格式化器
                    response_text = crawler.client.preview_downloader.format_preview_response(result)
                    
                    return {
                        "status": "success",
                        "result": response_text
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("error", "预览视频操作失败")
                    }
            else:
                return {
                    "status": "error",
                    "error": "预览视频功能不可用"
                }
        
        elif command == "SearchWithFilters":
            # 带过滤器的搜索命令
            keyword = request_data.get('keyword', '') or ''
            if isinstance(keyword, str):
                keyword = keyword.strip()
            else:
                keyword = str(keyword).strip() if keyword is not None else ''
            if not keyword:
                return {
                    "status": "error",
                    "error": "缺少 keyword 参数"
                }
            
            # 处理所有参数
            page = int(request_data.get('page', 1))
            sort = request_data.get('sort', '').strip()
            filter_type = request_data.get('filter', '').strip()
            include_cover = request_data.get('include_cover', True)
            include_title = request_data.get('include_title', True)
            max_results = int(request_data.get('max_results', 20))
            max_pages = int(request_data.get('max_pages', 1))
            
            # 处理增强信息参数
            enhanced_info = request_data.get('enhanced_info', False)
            if isinstance(enhanced_info, str):
                enhanced_info = enhanced_info.lower() in ['true', '1', 'yes', 'on']
            
            # 使用增强搜索功能
            if hasattr(crawler, 'client') and hasattr(crawler.client, 'search_videos_with_filters'):
                result = crawler.client.search_videos_with_filters(
                    keyword=keyword,
                    page=page,
                    sort=sort if sort else None,
                    filter_type=filter_type if filter_type else None,
                    include_cover=include_cover,
                    include_title=include_title,
                    max_results=max_results,
                    max_pages=max_pages,
                    enhanced_info=enhanced_info
                )
                
                if result.get("success"):
                    results = result["results"]
                    
                    # 构建响应文本
                    response_text = f"""### MissAV 增强搜索结果 ###

搜索关键词: {keyword}
页码: {page}"""
                    
                    if result.get('sort_name'):
                        response_text += f"\n排序方式: {result['sort_name']}"
                    
                    if result.get('filter_name'):
                        response_text += f"\n过滤器: {result['filter_name']}"
                    
                    response_text += f"\n找到视频数量: {result['total_count']}"
                    
                    if enhanced_info:
                        response_text += " (包含增强信息)"
                    
                    response_text += "\n\n"
                    
                    if results:
                        response_text += "搜索结果:\n\n"
                        for i, video in enumerate(results, 1):
                            response_text += f"{i}. **{video['title']}**\n"
                            response_text += f"   视频代码: {video['video_code']}\n"
                            response_text += f"   链接: {video['url']}\n"
                            
                            if include_cover and video.get('thumbnail'):
                                response_text += f"   封面图片: {video['thumbnail']}\n"
                            
                            # 显示增强信息
                            if enhanced_info:
                                if video.get('actresses'):
                                    actresses = video['actresses']
                                    if isinstance(actresses, list):
                                        response_text += f"   演员: {', '.join(actresses[:3])}{'...' if len(actresses) > 3 else ''}\n"
                                    else:
                                        response_text += f"   演员: {actresses}\n"
                                
                                if video.get('tags'):
                                    tags = video['tags']
                                    if isinstance(tags, list):
                                        response_text += f"   类型: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}\n"
                                    else:
                                        response_text += f"   类型: {tags}\n"
                                
                                if video.get('labels'):
                                    labels = video['labels']
                                    if isinstance(labels, list):
                                        response_text += f"   标签: {', '.join(labels)}\n"
                                    else:
                                        response_text += f"   标签: {labels}\n"
                                
                                if video.get('series'):
                                    response_text += f"   系列: {video['series']}\n"
                                
                                if video.get('studio'):
                                    response_text += f"   发行商: {video['studio']}\n"
                                
                                if video.get('maker'):
                                    response_text += f"   制作商: {video['maker']}\n"
                                
                                if video.get('duration') or video.get('precise_duration'):
                                    duration = video.get('precise_duration') or video.get('duration')
                                    response_text += f"   时长: {duration}\n"
                                
                                if video.get('release_date'):
                                    response_text += f"   发行日期: {video['release_date']}\n"
                                
                                # 显示可用分辨率
                                if video.get('available_resolutions'):
                                    resolutions = video['available_resolutions']
                                    if isinstance(resolutions, list) and resolutions:
                                        res_count = len(resolutions)
                                        response_text += f"   可用分辨率 ({res_count}个): "
                                        res_list = [f"{r['quality']} ({r['resolution']})" for r in resolutions[:4]]
                                        response_text += ", ".join(res_list)
                                        if len(resolutions) > 4:
                                            response_text += "..."
                                        response_text += "\n"
                                elif video.get('best_quality'):
                                    response_text += f"   最高画质: {video['best_quality']}\n"
                                
                                # 显示预览视频
                                if video.get('preview_videos'):
                                    previews = video['preview_videos']
                                    if isinstance(previews, list) and previews:
                                        response_text += f"   预览视频: 可用 ({len(previews)}个)\n"
                                        response_text += f"     主预览: {previews[0]}\n"
                                
                                # 显示M3U8播放链接
                                if video.get('main_m3u8'):
                                    response_text += f"   M3U8播放列表: {video['main_m3u8']}\n"
                                
                                if video.get('rating'):
                                    response_text += f"   评分: {video['rating']}\n"
                                
                                if video.get('views') or video.get('view_count'):
                                    views = video.get('views') or video.get('view_count')
                                    response_text += f"   观看次数: {views}\n"
                                
                                if video.get('description'):
                                    desc = video['description']
                                    # 适当限制描述长度，但保留更多内容
                                    if len(desc) > 300:
                                        desc = desc[:300] + "..."
                                    response_text += f"   简介: {desc}\n"
                            else:
                                # 基础信息
                                if video.get('publish_date'):
                                    response_text += f"   发布日期: {video['publish_date']}\n"
                            
                            response_text += "\n"

                    else:
                        response_text += "未找到相关视频。\n"
                    
                    response_text += "\n增强搜索完成！"
                    
                    return {
                        "status": "success",
                        "result": response_text
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("error", "增强搜索失败")
                    }
            else:
                return {
                    "status": "error",
                    "error": "增强搜索功能不可用"
                }
        
        elif command == "GetHotWithFilters":
            # 带过滤器的热榜命令 - 与SearchWithFilters看齐
            category = request_data.get('category', 'daily') or 'daily'
            page = int(request_data.get('page', 1))
            sort = request_data.get('sort', '').strip()
            filter_type = request_data.get('filter', '').strip()
            include_cover = request_data.get('include_cover', True)
            include_title = request_data.get('include_title', True)
            max_results = int(request_data.get('max_results', 20))
            max_pages = int(request_data.get('max_pages', 1))
            
            # 处理增强信息参数
            enhanced_info = request_data.get('enhanced_info', False)
            if isinstance(enhanced_info, str):
                enhanced_info = enhanced_info.lower() in ['true', '1', 'yes', 'on']
            
            # 使用增强热榜功能
            if hasattr(crawler, 'client') and hasattr(crawler.client, 'get_hot_videos_with_filters'):
                result = crawler.client.get_hot_videos_with_filters(
                    category=category,
                    page=page,
                    sort=sort if sort else None,
                    filter_type=filter_type if filter_type else None,
                    include_cover=include_cover,
                    include_title=include_title,
                    max_results=max_results,
                    max_pages=max_pages,
                    enhanced_info=enhanced_info
                )
                
                if result.get("success"):
                    results = result["results"]
                    category_name = {
                        'daily': '每日热门',
                        'weekly': '每周热门', 
                        'monthly': '每月热门',
                        'new': '最新视频',
                        'popular': '最受欢迎',
                        'trending': '趋势视频'
                    }.get(category, '热门视频')
                    
                    response_text = f"""### MissAV {category_name} ###

分类: {category_name}
页码: {page}"""
                    
                    if result.get('sort_name'):
                        response_text += f"\n排序方式: {result['sort_name']}"
                    
                    if result.get('filter_name'):
                        response_text += f"\n过滤器: {result['filter_name']}"
                    
                    response_text += f"\n找到视频数量: {result['total_count']}"
                    
                    if enhanced_info:
                        response_text += " (包含增强信息)"
                    
                    response_text += "\n\n"
                    
                    if results:
                        response_text += "热榜视频:\n\n"
                        for i, video in enumerate(results, 1):
                            response_text += f"{i}. **{video['title']}**\n"
                            response_text += f"   视频代码: {video['video_code']}\n"
                            response_text += f"   链接: {video['url']}\n"
                            
                            if include_cover and video.get('thumbnail'):
                                response_text += f"   封面图片: {video['thumbnail']}\n"
                            
                            # 显示增强信息
                            if enhanced_info:
                                if video.get('actresses'):
                                    actresses = video['actresses']
                                    if isinstance(actresses, list):
                                        response_text += f"   演员: {', '.join(actresses[:3])}{'...' if len(actresses) > 3 else ''}\n"
                                    else:
                                        response_text += f"   演员: {actresses}\n"
                                
                                if video.get('tags'):
                                    tags = video['tags']
                                    if isinstance(tags, list):
                                        response_text += f"   类型: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}\n"
                                    else:
                                        response_text += f"   类型: {tags}\n"
                                
                                if video.get('labels'):
                                    labels = video['labels']
                                    if isinstance(labels, list):
                                        response_text += f"   标签: {', '.join(labels)}\n"
                                    else:
                                        response_text += f"   标签: {labels}\n"
                                
                                if video.get('series'):
                                    response_text += f"   系列: {video['series']}\n"
                                
                                if video.get('studio'):
                                    response_text += f"   发行商: {video['studio']}\n"
                                
                                if video.get('maker'):
                                    response_text += f"   制作商: {video['maker']}\n"
                                
                                if video.get('duration') or video.get('precise_duration'):
                                    duration = video.get('precise_duration') or video.get('duration')
                                    response_text += f"   时长: {duration}\n"
                                
                                if video.get('release_date'):
                                    response_text += f"   发行日期: {video['release_date']}\n"
                                
                                # 显示可用分辨率
                                if video.get('available_resolutions'):
                                    resolutions = video['available_resolutions']
                                    if isinstance(resolutions, list) and resolutions:
                                        res_count = len(resolutions)
                                        response_text += f"   可用分辨率 ({res_count}个): "
                                        res_list = [f"{r['quality']} ({r['resolution']})" for r in resolutions[:4]]
                                        response_text += ", ".join(res_list)
                                        if len(resolutions) > 4:
                                            response_text += "..."
                                        response_text += "\n"
                                elif video.get('best_quality'):
                                    response_text += f"   最高画质: {video['best_quality']}\n"
                                
                                # 显示预览视频
                                if video.get('preview_videos'):
                                    previews = video['preview_videos']
                                    if isinstance(previews, list) and previews:
                                        response_text += f"   预览视频: 可用 ({len(previews)}个)\n"
                                        response_text += f"     主预览: {previews[0]}\n"
                                
                                # 显示M3U8播放链接
                                if video.get('main_m3u8'):
                                    response_text += f"   M3U8播放列表: {video['main_m3u8']}\n"
                                
                                if video.get('rating'):
                                    response_text += f"   评分: {video['rating']}\n"
                                
                                if video.get('views') or video.get('view_count'):
                                    views = video.get('views') or video.get('view_count')
                                    response_text += f"   观看次数: {views}\n"
                                
                                if video.get('description'):
                                    desc = video['description']
                                    # 适当限制描述长度，但保留更多内容
                                    if len(desc) > 300:
                                        desc = desc[:300] + "..."
                                    response_text += f"   简介: {desc}\n"
                            else:
                                # 基础信息
                                if video.get('duration'):
                                    response_text += f"   时长: {video['duration']}\n"
                                if video.get('publish_date'):
                                    response_text += f"   发布日期: {video['publish_date']}\n"
                            
                            response_text += "\n"

                    else:
                        response_text += "暂无热榜视频。\n"
                    
                    if result.get("note"):
                        response_text += f"\n💡 {result['note']}\n"
                    
                    response_text += "\n增强热榜获取完成！"
                    
                    return {
                        "status": "success",
                        "result": response_text
                    }
                else:
                    return {
                        "status": "error",
                        "error": result.get("error", "增强热榜获取失败")
                    }
            else:
                return {
                    "status": "error",
                    "error": "增强热榜功能不可用"
                }
        
        else:
            return {
                "status": "error",
                "error": f"未知命令: {command}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": f"处理请求时发生错误: {str(e)}",
            "traceback": traceback.format_exc()
        }


def main():
    """主函数"""
    try:
        # 读取标准输入
        input_data = sys.stdin.read().strip()
        
        if not input_data:
            result = {
                "status": "error",
                "error": "没有接收到输入数据"
            }
        else:
            try:
                # 解析JSON输入
                request_data = json.loads(input_data)
                result = process_request(request_data)
            except json.JSONDecodeError as e:
                result = {
                    "status": "error",
                    "error": f"JSON解析失败: {str(e)}"
                }
    
    except Exception as e:
        result = {
            "status": "error",
            "error": f"插件执行失败: {str(e)}",
            "traceback": traceback.format_exc()
        }
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False), file=sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()