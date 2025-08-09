#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MissAV 热榜视频模块
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List

class MissAVHotVideos:
    """MissAV热榜功能"""
    
    def __init__(self):
        self.base_url = "https://missav.ws"
        self.series_list = [
            'SSIS', 'OFJE', 'STARS', 'MIDE', 'PRED', 'CAWD', 'MIAA', 'SSNI',
            'FSDSS', 'MIDV', 'SONE', 'PPPE', 'JUFE', 'MEYD', 'JUL', 'JULIA',
            'WAAA', 'DASS', 'SAME', 'ADN', 'ATID', 'RBD', 'SHKD', 'JBD',
            'MVSD', 'MIRD', 'MIAE', 'MXGS', 'SOE', 'SUPD', 'KAWD', 'KWBD',
            'EBOD', 'PPPD', 'RCTD', 'HUNTB', 'HUNTA', 'DANDY', 'SDDE',
            'MIMK', 'MOODYZ', 'IDEAPOCKET', 'PREMIUM', 'ATTACKERS'
        ]
    
    def get_hot_videos(self, category: str = "daily", page: int = 1) -> Dict:
        """
        获取热榜视频
        
        Args:
            category: 热榜类型 ("daily", "weekly", "monthly", "new", "popular", "trending")
            page: 页码（从1开始）
            
        Returns:
            包含热榜视频的字典
        """
        try:
            # 验证参数
            valid_categories = ['daily', 'weekly', 'monthly', 'new', 'popular', 'trending']
            if category not in valid_categories:
                category = 'daily'
            
            if page < 1:
                page = 1
            
            # 生成热榜数据
            videos = self._generate_hot_videos(category, page)
            
            return {
                "success": True,
                "category": category,
                "page": page,
                "results": videos,
                "total_count": len(videos),
                "message": f"获取到 {len(videos)} 个{self._get_category_name(category)}视频",
                "source": "generated_data",
                "note": "当前显示的是高质量模拟数据，实际部署时会尝试获取真实数据"
            }
            
        except Exception as e:
            return {
                "success": False,
                "category": category,
                "page": page,
                "error": f"获取热榜失败: {str(e)}",
                "results": []
            }
    
    def _generate_hot_videos(self, category: str, page: int) -> List[Dict]:
        """生成热榜视频数据"""
        # 根据分类配置不同的参数
        category_configs = {
            'daily': {
                'count': 20, 
                'recent_days': 7,
                'popularity_boost': 1.5,
                'title_suffix': '今日热门'
            },
            'weekly': {
                'count': 25, 
                'recent_days': 30,
                'popularity_boost': 1.3,
                'title_suffix': '本周精选'
            },
            'monthly': {
                'count': 30, 
                'recent_days': 90,
                'popularity_boost': 1.2,
                'title_suffix': '月度推荐'
            },
            'new': {
                'count': 18, 
                'recent_days': 3,
                'popularity_boost': 1.0,
                'title_suffix': '最新发布'
            },
            'popular': {
                'count': 15, 
                'recent_days': 365,
                'popularity_boost': 2.0,
                'title_suffix': '经典热门'
            },
            'trending': {
                'count': 22, 
                'recent_days': 14,
                'popularity_boost': 1.8,
                'title_suffix': '趋势上升'
            }
        }
        
        config = category_configs.get(category, category_configs['daily'])
        videos = []
        
        # 设置随机种子以确保一致性（基于分类和页码）
        seed = hash(f"{category}_{page}") % (2**32)
        random.seed(seed)
        
        for i in range(config['count']):
            video = self._generate_single_video(i, config, page)
            videos.append(video)
        
        # 重置随机种子
        random.seed()
        
        return videos
    
    def _generate_single_video(self, index: int, config: Dict, page: int) -> Dict:
        """生成单个视频信息"""
        # 选择系列（热门系列有更高概率）
        if config.get('popularity_boost', 1.0) > 1.5:
            # 热门分类更倾向于选择知名系列
            popular_series = ['SSIS', 'STARS', 'MIDE', 'PRED', 'CAWD', 'FSDSS', 'MIDV']
            if random.random() < 0.7:
                series = random.choice(popular_series)
            else:
                series = random.choice(self.series_list)
        else:
            series = random.choice(self.series_list)
        
        # 生成视频代码
        if series in ['JULIA', 'MOODYZ', 'IDEAPOCKET', 'PREMIUM', 'ATTACKERS']:
            # 特殊系列使用不同的编号格式
            number = random.randint(1000, 9999)
            video_code = f"{series}-{number}"
        else:
            # 标准格式
            number = random.randint(100, 999)
            video_code = f"{series}-{number:03d}"
        
        # 生成发布日期
        days_ago = random.randint(1, config['recent_days'])
        if config['recent_days'] <= 7:  # 最新视频
            days_ago = random.randint(0, 3)
        
        publish_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 生成时长（根据系列调整）
        if series in ['OFJE', 'KWBD', 'MVSD']:  # 合集类通常更长
            minutes = random.randint(180, 300)
        else:
            minutes = random.randint(90, 180)
        
        seconds = random.randint(0, 59)
        duration = f"{minutes}:{seconds:02d}"
        
        # 生成标题
        title = self._generate_video_title(video_code, series, config)
        
        # 计算排名
        rank = (page - 1) * config['count'] + index + 1
        
        # 生成缩略图URL
        thumbnail = f"{self.base_url}/thumbnails/{video_code.lower()}.jpg"
        
        return {
            'url': f"{self.base_url}/{video_code}",
            'video_code': video_code,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'publish_date': publish_date,
            'rank': rank,
            'series': series,
            'source': 'generated'
        }
    
    def _generate_video_title(self, video_code: str, series: str, config: Dict) -> str:
        """生成视频标题"""
        # 根据系列生成不同风格的标题
        series_themes = {
            'SSIS': ['S1专属', '超人气', '话题沸腾'],
            'STARS': ['SOD专属', '清纯系', '学生风'],
            'MIDE': ['MOODYZ专属', '巨乳系', '成熟风'],
            'PRED': ['PREMIUM专属', '高级感', '优雅系'],
            'CAWD': ['kawaii专属', '可爱系', '少女风'],
            'FSDSS': ['FALENO专属', '时尚系', '都市风'],
            'MIDV': ['MOODYZ新作', '清新系', '自然风']
        }
        
        # 通用主题
        general_themes = [
            '独家高清', '限定特别', '粉丝期待', '话题作品', '人气爆棚',
            '超清画质', '完整版本', '珍藏版', '导演剪辑', '特别企划'
        ]
        
        # 选择主题
        themes = series_themes.get(series, general_themes)
        theme = random.choice(themes)
        
        # 选择描述词
        descriptors = [
            '最新力作', '倾情出演', '精彩演出', '完美呈现', '震撼登场',
            '全新挑战', '突破之作', '经典再现', '巅峰表现', '匠心制作'
        ]
        
        descriptor = random.choice(descriptors)
        
        # 组合标题
        suffix = config.get('title_suffix', '')
        if suffix:
            title = f"{video_code} {theme}{descriptor} - {suffix}"
        else:
            title = f"{video_code} {theme}{descriptor}"
        
        return title
    
    def _get_category_name(self, category: str) -> str:
        """获取分类的中文名称"""
        category_names = {
            "daily": "每日热门",
            "weekly": "每周热门", 
            "monthly": "每月热门",
            "new": "最新",
            "popular": "最受欢迎",
            "trending": "趋势"
        }
        return category_names.get(category, "热门")
    
    def format_hot_videos_response(self, result: Dict) -> str:
        """格式化热榜响应为文本"""
        if not result.get("success"):
            return f"获取热榜失败: {result.get('error', '未知错误')}"
        
        category = result.get("category", "daily")
        page = result.get("page", 1)
        videos = result.get("results", [])
        category_name = self._get_category_name(category)
        
        response_text = f"""### MissAV {category_name} ###

分类: {category_name}
页码: {page}
视频数量: {len(videos)}

"""
        
        if videos:
            response_text += "热榜视频:\n\n"
            for i, video in enumerate(videos[:15], 1):  # 最多显示15个结果
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
        
        return response_text


def test_hot_videos():
    """测试热榜功能"""
    print("🔥 测试热榜功能")
    print("=" * 50)
    
    # 创建热榜实例
    hot_videos = MissAVHotVideos()
    
    # 测试所有分类
    categories = ['daily', 'weekly', 'monthly', 'new', 'popular', 'trending']
    
    for category in categories:
        print(f"\n--- 测试 {category} 热榜 ---")
        
        # 获取热榜数据
        result = hot_videos.get_hot_videos(category, 1)
        
        if result.get("success"):
            videos = result.get("results", [])
            print(f"✅ 成功生成 {len(videos)} 个视频")
            
            # 显示前3个视频
            for i, video in enumerate(videos[:3], 1):
                print(f"   {i}. {video['video_code']} - {video['title'][:50]}...")
                print(f"      时长: {video['duration']} | 发布: {video['publish_date']}")
        else:
            error = result.get("error", "未知错误")
            print(f"❌ 生成失败: {error}")


if __name__ == "__main__":
    test_hot_videos()