#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能字幕下载模块
严格照搬subtitlecatSubsDownloader-master/main.py的完整逻辑
"""

import os
import re
import requests
import time
import shutil
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import traceback

# 严格照搬原始依赖导入
try:
    import pysrt
    from langdetect import detect, LangDetectException
except ImportError:
    print("!!! 致命错误：缺少必要的库。请先运行 'pip install pysrt langdetect' 进行安装。")
    pysrt = None
    detect = None
    LangDetectException = Exception

# 严格照搬原始配置常量
baseSearchLink = "https://www.subtitlecat.com/index.php?search="
baseLink = "https://www.subtitlecat.com/"

# 严格照搬原始重试策略配置
MAX_REQUEST_RETRIES = 5
REQUEST_RETRY_DELAY_S = 10
MAX_DOWNLOAD_RETRIES = 5
DOWNLOAD_RETRY_DELAY_S = 5
REQUEST_TIMEOUT = 300000

# 严格照搬原始语言配置
LANG_CONFIG = {
    'chi_sim': {'name': '简体中文', 'id': 'download_zh-CN'},
    'chi_tra': {'name': '繁体中文', 'id': 'download_zh-TW'},
    'jpn': {'name': '日本語', 'id': 'download_ja'},
    'kor': {'name': '한국어', 'id': 'download_ko'},
    'eng': {'name': '英文', 'id': 'download_en'}
}
DETECT_MAP = {'ja':'jpn', 'ko':'kor', 'en':'eng', 'zh-cn':'chi_sim', 'zh-tw':'chi_tra'}

# 严格照搬原始异常类
class LogicalFailureException(Exception):
    pass

class SubtitleDownloader:
    """严格照搬原始逻辑的字幕下载器"""
    
    def __init__(self):
        # 创建session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search_local_subtitle(self, video_code: str) -> Optional[str]:
        """
        在本地字幕库中搜索字幕
        
        Args:
            video_code: 视频番号（不带后缀），如 SDDE-475
            
        Returns:
            字幕文件路径，如果找到的话
        """
        try:
            # 本地字幕索引文件路径
            index_file = Path(__file__).parent.parent / "local_subtitles_src" / "index.txt"
            subtitles_dir = Path(__file__).parent.parent / "local_subtitles_src" / "subtitles"
            
            if not index_file.exists():
                return None
            
            # 读取索引文件
            with open(index_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 搜索匹配的字幕文件
            video_code_upper = video_code.upper()
            video_code_lower = video_code.lower()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析行格式：FILENAME.srt <- @ORIGINAL_FILENAME.srt 或 FILENAME.srt <- ORIGINAL_FILENAME.srt
                if '<-' in line:
                    parts = line.split('<-', 1)
                    if len(parts) == 2:
                        target_file = parts[0].strip()
                        source_file = parts[1].strip()
                        
                        # 移除可能的@符号
                        if source_file.startswith('@'):
                            source_file = source_file[1:]
                        
                        # 检查是否匹配视频代码
                        if (video_code_upper in target_file.upper() or 
                            video_code_lower in target_file.lower() or
                            video_code_upper in source_file.upper() or
                            video_code_lower in source_file.lower()):
                            
                            # 构建完整路径
                            subtitle_path = subtitles_dir / target_file
                            if subtitle_path.exists():
                                return str(subtitle_path)
                            
                            # 如果目标文件不存在，尝试源文件
                            source_path = subtitles_dir / source_file
                            if source_path.exists():
                                return str(source_path)
                else:
                    # 简单格式：直接是文件名
                    if (video_code_upper in line.upper() or 
                        video_code_lower in line.lower()):
                        subtitle_path = subtitles_dir / line
                        if subtitle_path.exists():
                            return str(subtitle_path)
            
            return None
            
        except Exception as e:
            print(f"搜索本地字幕时出错: {str(e)}")
            return None
    
    def download_subtitle_with_retry(self, download_url: str, save_path: str) -> bool:
        """严格照搬原始的带重试逻辑的下载函数"""
        for attempt in range(MAX_DOWNLOAD_RETRIES):
            try:
                response = requests.get(download_url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 404: 
                    return False
                if response.status_code == 200 and len(response.content) > 10:
                    with open(save_path, 'wb') as file: 
                        file.write(response.content)
                    return True
            except requests.exceptions.RequestException: 
                pass
            if attempt < MAX_DOWNLOAD_RETRIES - 1: 
                time.sleep(DOWNLOAD_RETRY_DELAY_S)
        return False
    
    def scrape_and_create_srt_from_raw_html(self, page_html: str, save_path: str) -> bool:
        """严格照搬原始的通过分割原始HTML来抓取原文并创建SRT文件，带内容验证"""
        try:
            key_phrase = "These are the user uploaded subtitles that are being translated:"
            parts = page_html.split(key_phrase, 1)
            if len(parts) < 2: 
                return False
            content_after_phrase = parts[1]
            footer_tag = '<div class="footer">'
            sub_html_part = content_after_phrase.split(footer_tag, 1)[0]
            soup = BeautifulSoup(sub_html_part, "html.parser")
            srt_content = soup.get_text().strip()
            if not srt_content or "-->" not in srt_content:
                return False
            with open(save_path, 'w', encoding='utf-8') as f: 
                f.write(srt_content)
            return True
        except Exception:
            return False
    
    def create_dual_language_ass(self, original_info: dict, translated_info: dict, final_ass_path: str) -> bool:
        """严格照搬原始的创建专业的双语ASS文件"""
        try:
            original_subs = pysrt.open(original_info['path'], encoding='utf-8')
            translated_subs = pysrt.open(translated_info['path'], encoding='utf-8')
            with open(final_ass_path, 'w', encoding='utf-8') as ass_file:
                ass_file.write("[Script Info]\nTitle: Dual Language Subtitle\nScriptType: v4.00+\nWrapStyle: 0\nPlayResX: 1280\nPlayResY: 720\n\n")
                ass_file.write("[V4+ Styles]\n")
                ass_file.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                ass_file.write("Style: Bottom,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,15,1\n")
                ass_file.write("Style: Top,Arial,36,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,8,10,10,15,1\n\n")
                ass_file.write("[Events]\n")
                ass_file.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                for sub_t, sub_o in zip(translated_subs, original_subs):
                    start, end = (sub_t.start.to_time().strftime('%H:%M:%S.%f')[:-4], sub_t.end.to_time().strftime('%H:%M:%S.%f')[:-4])
                    text_t, text_o = (sub_t.text.replace('\n', '\\N'), sub_o.text.replace('\n', '\\N'))
                    ass_file.write(f"Dialogue: 0,{start},{end},Bottom,,0,0,0,,{text_t}\n")
                    ass_file.write(f"Dialogue: 0,{start},{end},Top,,0,0,0,,{text_o}\n")
            return True
        except Exception:
            return False
    
    def process_single_code_with_internal_retries(self, code: str, temp_path: str, output_dir: str, filename_base: str) -> Tuple[bool, str]:
        """严格照搬原始的最终版逻辑，包含基于内容检测和网页抓取的优先级决策"""
        for attempt in range(MAX_REQUEST_RETRIES):
            try:
                search_url = baseSearchLink + code
                r = requests.get(search_url, timeout=REQUEST_TIMEOUT)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                sub_page_links = [link.get('href') for link in soup.find_all('a', href=True) if code.lower() in link.get('href').lower()]
                if not sub_page_links: 
                    raise LogicalFailureException(f"网站上未能搜索到 {code} 的任何相关字幕记录。")

                page_info_list = []
                key_phrase = "These are the user uploaded subtitles that are being translated:"
                
                for i, page_link in enumerate(sub_page_links):
                    subURL = baseLink + page_link
                    try:
                        page_r = requests.get(subURL, timeout=REQUEST_TIMEOUT)
                        page_r.raise_for_status()
                        page_html_content = page_r.text
                        page_soup = BeautifulSoup(page_html_content, "html.parser")
                        page_text_for_detect = page_soup.get_text()
                        phrase_index = page_text_for_detect.find(key_phrase)
                        detected_lang_key = 'unknown'
                        
                        if phrase_index != -1:
                            sample_start = phrase_index + len(key_phrase)
                            sample_text_for_validation = page_text_for_detect[sample_start : sample_start + 400].strip()
                            if "File Not Found" in sample_text_for_validation or "-->" not in sample_text_for_validation:
                                continue

                            try:
                                lang_code = detect(sample_text_for_validation)
                                if lang_code in DETECT_MAP: 
                                    detected_lang_key = DETECT_MAP[lang_code]
                            except LangDetectException: 
                                pass
                        
                        available_downloads = {}
                        for lang_key, lang_data in LANG_CONFIG.items():
                             if (tag := page_soup.find('a', id=lang_data['id'])):
                                available_downloads[lang_key] = {'name': lang_data['name'], 'link': baseLink + tag.get('href')}
                        
                        if available_downloads:
                            page_info_list.append({'url': subURL, 'html': page_html_content, 'detected_lang': detected_lang_key, 'downloads': available_downloads})
                    except requests.exceptions.RequestException: 
                        pass
                
                if not page_info_list: 
                    raise LogicalFailureException("侦察完毕，但所有详情页都无法访问或没有可用字幕。")

                # 严格照搬原始的优先级处理逻辑
                def handle_bilingual_case(page, priority_name):
                    chi_sub = page['downloads'].get('chi_sim') or page['downloads'].get('chi_tra')
                    chi_path = os.path.join(temp_path, f"{code}_chi.srt")
                    if not self.download_subtitle_with_retry(chi_sub['link'], chi_path): 
                        return False, "下载中文字幕失败"
                    
                    original_sub_info = None
                    original_path = os.path.join(temp_path, f"{code}_orig.srt")
                    detected_lang_key = page['detected_lang']
                    
                    if detected_lang_key != 'unknown' and detected_lang_key in page['downloads']:
                        original_download_info = page['downloads'][detected_lang_key]
                        if self.download_subtitle_with_retry(original_download_info['link'], original_path):
                            original_sub_info = {'name': original_download_info['name'], 'path': original_path}
                    
                    if not original_sub_info and detected_lang_key != 'unknown':
                        if self.scrape_and_create_srt_from_raw_html(page['html'], original_path):
                            original_sub_info = {'name': LANG_CONFIG.get(detected_lang_key, {}).get('name', '原文抓取'), 'path': original_path}

                    if original_sub_info:
                        final_ass_path = os.path.join(output_dir, f"{filename_base}.ass")
                        if self.create_dual_language_ass(original_sub_info, {'name': chi_sub['name'], 'path': chi_path}, final_ass_path):
                            return True, f"双语字幕 ({priority_name}/{chi_sub['name']})"
                    
                    shutil.copy(chi_path, os.path.join(output_dir, f"{filename_base}.srt"))
                    return True, f"中文字幕: {chi_sub['name']} (双语创建失败)"

                # 严格照搬原始优先级 1: 中文优先
                for page in page_info_list:
                    if page['detected_lang'] in ['chi_sim', 'chi_tra'] and (chi_sub := page['downloads'].get('chi_sim') or page['downloads'].get('chi_tra')):
                        chi_path = os.path.join(temp_path, f"{code}_chi.srt")
                        if self.download_subtitle_with_retry(chi_sub['link'], chi_path):
                            shutil.copy(chi_path, os.path.join(output_dir, f"{filename_base}.srt"))
                            
                            # 严格照搬原始的附加任务：检查日语原声页面
                            for jpn_page in page_info_list:
                                if jpn_page['detected_lang'] == 'jpn':
                                    jpn_path = os.path.join(temp_path, f"{code}_jpn_addon.srt")
                                    if 'jpn' in jpn_page['downloads'] and self.download_subtitle_with_retry(jpn_page['downloads']['jpn']['link'], jpn_path):
                                        pass  # 只下载到temp_subs，不再复制
                                    elif self.scrape_and_create_srt_from_raw_html(jpn_page['html'], jpn_path):
                                        pass  # 只下载到temp_subs，不再复制
                                    break
                            return True, f"中文原声字幕: {chi_sub['name']}"

                # 严格照搬原始优先级 2: 日语优先
                for page in page_info_list:
                    if page['detected_lang'] == 'jpn' and (page['downloads'].get('chi_sim') or page['downloads'].get('chi_tra')):
                        result = handle_bilingual_case(page, "日语优先")
                        if result[0]:
                            return result
                
                # 严格照搬原始优先级 3: 英语优先
                for page in page_info_list:
                    if page['detected_lang'] == 'eng' and (page['downloads'].get('chi_sim') or page['downloads'].get('chi_tra')):
                        result = handle_bilingual_case(page, "英语优先")
                        if result[0]:
                            return result
                
                # 严格照搬原始优先级 4: 任何可用的中文字幕
                for page in page_info_list:
                    if (chi_sub := page['downloads'].get('chi_sim') or page['downloads'].get('chi_tra')):
                        if self.download_subtitle_with_retry(chi_sub['link'], os.path.join(temp_path, f"{code}_chi.srt")):
                            shutil.copy(os.path.join(temp_path, f"{code}_chi.srt"), os.path.join(output_dir, f"{filename_base}.srt"))
                            return True, f"中文字幕: {chi_sub['name']}"

                raise LogicalFailureException("已分析所有结果，但未能根据任何优先级成功下载字幕。")
            except (requests.exceptions.RequestException, LogicalFailureException) as e:
                if attempt < MAX_REQUEST_RETRIES - 1: 
                    time.sleep(REQUEST_RETRY_DELAY_S)
                else: 
                    return False, f"处理 {code} 时遇到问题: {e}"
        
        return False, "达到最大重试次数"
    

    
    def download_subtitle(self, video_code: str, output_dir: str, filename_base: str) -> Tuple[bool, str]:
        """
        严格照搬原始逻辑的智能下载字幕主函数
        
        Args:
            video_code: 视频番号（不带后缀），如 SDDE-475
            output_dir: 输出目录（与视频文件同一文件夹）
            filename_base: 输出文件名基础（不含扩展名）
            
        Returns:
            (是否成功, 简化状态信息)
        """
        if not pysrt or not detect:
            return False, "缺少必要的依赖库 (pysrt, langdetect)"
        
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 1. 首先搜索本地字幕库
            local_subtitle = self.search_local_subtitle(video_code)
            if local_subtitle:
                # 复制本地字幕到输出目录（与视频同一文件夹）
                local_path = Path(local_subtitle)
                output_path = Path(output_dir) / f"{filename_base}{local_path.suffix}"
                shutil.copy(local_subtitle, output_path)
                return True, "本地字幕"
            
            # 2. 如果本地没有，从网络下载（严格照搬原始逻辑）
            temp_dir = os.path.join(output_dir, "temp_subs")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                success, message = self.process_single_code_with_internal_retries(video_code, temp_dir, output_dir, filename_base)
                
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                
                if success:
                    return True, "网络下载"
                else:
                    return False, message
                    
            except Exception as e:
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                raise e
                
        except Exception as e:
            return False, f"字幕下载出错: {str(e)}"

def extract_video_code_from_title_or_url(title: str, url: str = "") -> Optional[str]:
    """
    从视频标题或URL中提取视频番号
    
    Args:
        title: 视频标题
        url: 视频URL（可选）
        
    Returns:
        提取的视频番号，如果找不到则返回None
    """
    # 常见的视频番号模式
    patterns = [
        r'\b([A-Z]{2,6}-\d{2,4})\b',  # 如 SSIS-950, OFJE-505
        r'\b(\d{2,4}[A-Z]{2,6}-\d{2,4})\b',  # 如 259LUXU-1234
        r'\b(FC2-PPV-\d{6,8})\b',  # 如 FC2-PPV-1234567
        r'\b([A-Z]{1,4}\d{2,4})\b',  # 如 ABP123
        r'\b([a-z]{2,6}-\d{2,4})\b',  # 小写格式
    ]
    
    # 先从标题中提取
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    # 如果标题中没有，尝试从URL中提取
    if url:
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()
    
    return None