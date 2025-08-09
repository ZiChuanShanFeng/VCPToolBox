# MissAVCrawl Plugin

<div align="center">

![MissAVCrawl](https://img.shields.io/badge/MissAVCrawl-v2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![VCP](https://img.shields.io/badge/VCP-Compatible-purple.svg)

**功能强大的 MissAV 视频爬虫插件，支持智能搜索、异步下载、字幕获取等全方位功能**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [命令详解](#-命令详解) • [高级功能](#-高级功能) • [开发文档](#-开发文档)

</div>

---

## 🌟 功能特性

### 🎬 视频处理
- **智能信息提取**: 自动获取视频标题、番号、演员、标签等详细信息
- **多质量下载**: 支持最高画质、指定分辨率等多种下载选项
- **异步下载**: 支持后台异步下载，实时进度反馈
- **预览视频**: 获取和下载视频预览片段

### 🔍 搜索功能
- **关键词搜索**: 支持演员名、番号、标题等多维度搜索
- **高级过滤**: 按类型、时长、发布日期等条件筛选
- **排序选项**: 支持按观看量、发布时间、收藏数等排序
- **分页浏览**: 支持多页结果获取

### 🔥 热门内容
- **多种分类**: 日榜、周榜、月榜、最新、趋势等
- **专题内容**: 中文字幕、无码流出、特定系列等
- **实时更新**: 基于真实网站数据的热门内容

### 📝 智能字幕
- **本地字幕库**: 优先使用本地字幕资源
- **网络爬取**: 自动从字幕网站获取中文字幕
- **多语言支持**: 支持中文、日语、英语等多种语言
- **双语字幕**: 自动生成ASS格式双语字幕文件
- **并行下载**: 字幕下载与视频下载同时进行

### 🛡️ 技术特性
- **反爬虫机制**: 智能User-Agent轮换、请求间隔控制
- **错误恢复**: 自动重试机制，网络异常自动恢复
- **缓存优化**: 智能缓存机制，提升响应速度
- **进度追踪**: 实时下载进度和状态更新

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 网络连接
- 足够的存储空间

### 安装步骤

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境**（可选）
```bash
cp config.env.example config.env
# 编辑 config.env 文件设置下载目录等参数
```

3. **验证安装**
```bash
python plugin_main.py
# 输入测试命令验证功能
```

### 基础使用

```bash
# 获取视频信息
echo '{"command": "GetVideoInfo", "url": "https://missav.ws/ssis-834"}' | python plugin_main.py

# 搜索视频
echo '{"command": "SearchVideos", "keyword": "三上悠亜", "page": 1}' | python plugin_main.py

# 异步下载视频
echo '{"command": "DownloadVideoAsync", "url": "https://missav.ws/ssis-834", "quality": "best"}' | python plugin_main.py
```

---

## 📋 命令详解

### 🎬 GetVideoInfo - 获取视频信息

获取指定视频的详细信息，包括标题、演员、标签、播放链接等。

**请求格式:**
```json
{
  "command": "GetVideoInfo",
  "url": "https://missav.ws/video-url"
}
```

**响应示例:**
```
### MissAV 视频信息 ###

**标题**: SSIS-834 完整退休 AV 女優最後一天
**番号**: SSIS-834
**演员**: 三上悠亜
**发行日期**: 2023-08-15
**时长**: 02:30:15
**类型**: 單人作品, 巨乳, 薄馬賽克
**系列**: S1 NO.1 STYLE
**发行商**: S1 NO.1 STYLE
**M3U8播放列表**: https://...
```

### 🔍 SearchVideos - 搜索视频

支持关键词搜索，可指定排序方式、过滤条件等高级选项。

**请求格式:**
```json
{
  "command": "SearchVideos",
  "keyword": "搜索关键词",
  "page": 1,
  "sort": "views",
  "filter": "chinese_subtitle",
  "max_results": 20,
  "enhanced_info": true
}
```

**参数说明:**
- `keyword`: 搜索关键词（必需）
- `page`: 页码，默认1
- `sort`: 排序方式
  - `views`: 按观看量排序
  - `released_at`: 按发布时间排序
  - `saved`: 按收藏数排序
  - `today_views`: 按今日观看量排序
- `filter`: 过滤条件
  - `all`: 全部内容
  - `chinese_subtitle`: 中文字幕
  - `uncensored`: 无码影片
  - `single`: 单人作品
- `enhanced_info`: 是否获取增强信息（演员、标签等）

### 🔥 GetHotVideos - 获取热门视频

获取各种分类的热门视频内容。

**请求格式:**
```json
{
  "command": "GetHotVideos",
  "category": "daily",
  "page": 1,
  "sort": "views",
  "filter": "all"
}
```

**支持的分类:**
- `daily`: 每日热门
- `weekly`: 每周热门
- `monthly`: 每月热门
- `new`: 最新视频
- `chinese_subtitle`: 中文字幕专区
- `uncensored_leak`: 无码流出
- `siro`: SIRO系列
- `luxu`: LUXU系列

### 📥 DownloadVideo - 同步下载

同步下载视频文件，适合单个文件下载。

**请求格式:**
```json
{
  "command": "DownloadVideo",
  "url": "https://missav.ws/video-url",
  "quality": "best",
  "download_dir": "/path/to/download"
}
```

**质量选项:**
- `best`: 最高画质
- `1080p`: 1080P画质
- `720p`: 720P画质
- `480p`: 480P画质

### 🚀 DownloadVideoAsync - 异步下载

异步下载视频，支持实时进度更新和智能字幕下载。

**请求格式:**
```json
{
  "command": "DownloadVideoAsync",
  "url": "https://missav.ws/video-url",
  "quality": "best",
  "download_dir": "/path/to/download"
}
```

**特色功能:**
- ✅ 实时进度显示
- ✅ 自动字幕下载
- ✅ 断点续传支持
- ✅ 并行处理优化

**进度显示示例:**
```
📥 下载中: 45.2% (1205/2667)
📺 SSIS-834 完整退休 AV 女優最後一天 (SSIS-834)
⏱️ 剩余: 约 3.2 分钟
🔍 字幕搜索中...
```

### 🎯 GetEnhancedVideoInfo - 增强信息获取

获取更详细的视频信息，包括演员详情、相关视频等。

**请求格式:**
```json
{
  "command": "GetEnhancedVideoInfo",
  "url": "https://missav.ws/video-url",
  "use_cache": true
}
```

### 🎬 GetPreviewVideos - 预览视频

获取视频的预览片段信息，可选择下载。

**请求格式:**
```json
{
  "command": "GetPreviewVideos",
  "url": "https://missav.ws/video-url",
  "download": false,
  "output_dir": "/path/to/previews"
}
```

### 🔍 SearchWithFilters - 高级搜索

带过滤器的高级搜索功能，支持更精确的搜索条件。

**请求格式:**
```json
{
  "command": "SearchWithFilters",
  "keyword": "搜索关键词",
  "page": 1,
  "sort": "views",
  "filter": "chinese_subtitle",
  "enhanced_info": true,
  "max_results": 50,
  "max_pages": 3
}
```

---

## 🎯 高级功能

### 📝 智能字幕系统

插件内置了强大的字幕下载系统，基于 `subtitlecatSubsDownloader` 项目的核心逻辑：

#### 字幕获取策略
1. **本地字幕库优先**: 首先搜索 `local_subtitles_src/` 目录
2. **网络智能爬取**: 自动从 subtitlecat.com 获取字幕
3. **语言优先级**:
   - 中文原声字幕（最高优先级）
   - 日语原声 + 中文翻译（双语ASS）
   - 英语原声 + 中文翻译（双语ASS）
   - 任何可用的中文字幕

#### 字幕格式支持
- **SRT格式**: 标准字幕格式，兼容性最好
- **ASS格式**: 高级字幕格式，支持双语显示和样式控制

#### 并行下载优化
- 字幕搜索与视频下载同时开始
- 实时状态更新：🔍 搜索中 → ✅ 下载完成
- 智能文件命名，与视频文件匹配

#### 本地字幕库配置

在 `local_subtitles_src/index.txt` 中配置本地字幕映射：

```
SSIS-834.srt <- @SSIS-834_original.srt
SSNI-009.srt <- SSNI-009_chinese.srt
MIDE-486.srt <- MIDE-486_subtitle.srt
```

### 🛡️ 反爬虫机制

#### 多重防护策略
- **User-Agent轮换**: 5种不同的浏览器标识
- **请求间隔控制**: 智能延迟避免频率限制
- **Referer伪装**: 模拟真实浏览器行为
- **Session管理**: 维持会话状态

#### 错误恢复机制
- **自动重试**: 网络请求失败自动重试（最多5次）
- **指数退避**: 重试间隔逐渐增加
- **优雅降级**: 部分功能失败不影响其他功能

### 📊 缓存优化

#### 智能缓存策略
- **信息缓存**: 视频信息缓存24小时
- **预览缓存**: 预览图片本地缓存
- **搜索缓存**: 搜索结果短期缓存

#### 缓存管理
- 自动清理过期缓存
- 支持手动清理缓存
- 缓存大小限制

---

## 🔧 配置选项

### 环境变量配置

在 `config.env` 文件中可以配置以下选项：

```bash
# 下载配置
MISSAV_DOWNLOAD_DIR=/path/to/downloads
MISSAV_MAX_CONCURRENT_DOWNLOADS=3
MISSAV_MIN_FILE_SIZE_MB=10

# 网络配置
MISSAV_REQUEST_TIMEOUT=30
MISSAV_MAX_RETRIES=5
MISSAV_RETRY_DELAY=10

# 进度更新配置
MISSAV_PROGRESS_UPDATE_INTERVAL=2
MISSAV_SEGMENT_UPDATE_INTERVAL=25

# 字幕配置
MISSAV_SUBTITLE_ENABLED=true
MISSAV_SUBTITLE_LANGUAGES=zh-CN,ja,en
```

### 质量设置

支持的视频质量选项：
- `best`: 自动选择最高画质
- `1080p`: 1920x1080分辨率
- `720p`: 1280x720分辨率
- `480p`: 854x480分辨率
- `360p`: 640x360分辨率

### 下载器选项

支持的下载器类型：
- `threaded`: 多线程下载（推荐）
- `single`: 单线程下载
- `aria2c`: 使用aria2c下载器（需要安装）

---

## 🏗️ 开发文档

### 项目架构

```
Plugin/MissAVCrawl/
├── 📄 plugin_main.py              # VCP插件入口
├── 📄 request_handler.py          # 同步命令处理
├── 📄 base_api.py                 # 基础HTTP客户端
├── 📁 missav_api_core/            # 核心功能模块
│   ├── 📄 async_handler.py        # 异步下载处理
│   ├── 📄 subtitle_downloader.py  # 智能字幕下载
│   ├── 📄 crawler.py              # 爬虫核心逻辑
│   ├── 📄 missav_api.py           # MissAV API封装
│   ├── 📄 search_engine.py        # 搜索引擎
│   ├── 📄 hot_videos.py           # 热门视频
│   ├── 📄 enhanced_hot_videos.py  # 增强热门视频
│   ├── 📄 enhanced_info_extractor.py # 增强信息提取
│   ├── 📄 preview_downloader.py   # 预览视频下载
│   ├── 📄 unified_search_module.py # 统一搜索模块
│   ├── 📄 sort_filter_module.py   # 排序过滤模块
│   ├── 📄 async_downloader.py     # 异步下载器
│   ├── 📄 progress_handler.py     # 进度处理器
│   ├── 📄 network_utils.py        # 网络工具
│   └── 📄 consts.py               # 常量定义
└── 📁 local_subtitles_src/        # 本地字幕库
```

### 核心类说明

#### MissAVCrawler
主要的爬虫类，提供统一的API接口。

```python
from missav_api_core import MissAVCrawler

crawler = MissAVCrawler()
result = crawler.get_video_info("https://missav.ws/video-url")
```

#### SubtitleDownloader
智能字幕下载器，支持本地和网络字幕获取。

```python
from missav_api_core.subtitle_downloader import SubtitleDownloader

downloader = SubtitleDownloader()
success, message = downloader.download_subtitle("SSIS-834", "/output/dir", "filename")
```

#### BaseCore
基础HTTP客户端，提供反爬虫和错误恢复功能。

```python
from base_api import BaseCore

core = BaseCore()
response = core.get("https://example.com")
```

### 扩展开发

#### 添加新命令

1. 在 `request_handler.py` 中添加命令处理逻辑
2. 在相应的核心模块中实现功能
3. 更新文档和测试

#### 自定义字幕源

1. 继承 `SubtitleDownloader` 类
2. 重写 `download_subtitle_from_web` 方法
3. 实现自定义的字幕获取逻辑

---

## 📊 性能优化

### 下载性能
- **多线程下载**: 支持分段并行下载
- **断点续传**: 网络中断后自动恢复
- **智能重试**: 失败片段自动重试
- **带宽控制**: 可配置下载速度限制

### 内存优化
- **流式处理**: 大文件流式下载，减少内存占用
- **缓存管理**: 智能缓存清理，避免内存泄漏
- **资源回收**: 及时释放网络连接和文件句柄

### 网络优化
- **连接复用**: HTTP连接池复用
- **压缩传输**: 支持gzip压缩
- **DNS缓存**: 减少DNS查询时间

---

## 🐛 故障排除

### 常见问题

#### 1. 403 Forbidden 错误
**原因**: 反爬虫机制触发
**解决**: 
- 增加请求间隔时间
- 更换User-Agent
- 检查IP是否被封禁

#### 2. 字幕下载失败
**原因**: 字幕网站访问异常
**解决**:
- 检查网络连接
- 尝试使用本地字幕库
- 手动下载字幕文件

#### 3. 视频下载中断
**原因**: 网络不稳定或服务器限制
**解决**:
- 启用断点续传
- 降低并发下载数
- 检查存储空间

#### 4. 依赖库安装失败
**原因**: Python环境或网络问题
**解决**:
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或者单独安装问题库
pip install requests beautifulsoup4 lxml m3u8 pysrt langdetect
```

### 调试模式

启用详细日志输出：
```bash
export MISSAV_DEBUG=true
python plugin_main.py
```

---

## 📦 依赖说明

### 核心依赖
```
requests>=2.31.0          # HTTP请求库
httpx>=0.24.0             # 异步HTTP客户端
beautifulsoup4>=4.12.0    # HTML解析
lxml>=4.9.0               # XML/HTML解析器
m3u8>=3.5.0               # M3U8播放列表处理
```

### 字幕功能依赖
```
pysrt>=1.1.2              # SRT字幕文件处理
langdetect>=1.0.9         # 语言检测
tqdm>=4.66.0              # 进度条显示
```

### 可选依赖
```
aria2p>=0.11.3            # aria2c下载器支持
Pillow>=10.0.0            # 图片处理
python-dotenv>=1.0.0      # 环境变量管理
```

---

## 🤝 贡献指南

### 贡献方式
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 编写单元测试
- 更新相关文档

### 问题报告
提交 Issue 时请包含：
- 详细的问题描述
- 复现步骤
- 错误日志
- 系统环境信息

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [subtitlecatSubsDownloader](https://github.com/example/subtitlecatSubsDownloader) - 字幕下载核心逻辑
- [missAV_api](https://github.com/example/missAV_api) - API接口参考
- 所有贡献者和用户的支持

---

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/your-username/MissAVCrawl)
- 问题反馈: [GitHub Issues](https://github.com/your-username/MissAVCrawl/issues)
- 功能建议: [GitHub Discussions](https://github.com/your-username/MissAVCrawl/discussions)

---

## 📈 版本历史

### v2.0.0 (当前版本)
- ✅ 完全重构插件架构
- ✅ 新增智能字幕下载功能
- ✅ 支持并行字幕和视频下载
- ✅ 增强反爬虫机制
- ✅ 优化异步下载性能
- ✅ 新增预览视频功能
- ✅ 支持高级搜索过滤

### v1.0.0
- ✅ 基础视频信息获取
- ✅ 简单搜索功能
- ✅ 热门视频获取
- ✅ 基础下载功能

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个星标！**

Made with ❤️ by MissAVCrawl Team

</div>