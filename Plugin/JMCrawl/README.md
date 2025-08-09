# JMCrawl VCP Plugin

基于 JMComic-Crawler-Python 的禁漫天堂漫画下载 VCP 插件。

## 功能特性

- 🔍 **搜索本子**: 根据关键词搜索漫画作品
- 📖 **获取信息**: 查看本子的详细信息（作者、标签、章节等）
- 📚 **下载本子**: 下载完整的漫画本子（包含所有章节）
- 📄 **下载章节**: 下载指定的单个章节
- ⚙️ **灵活配置**: 支持自定义下载目录、图片格式、代理等

## 安装依赖

在插件目录下运行：

```bash
pip install -r requirements.txt
```

或者确保项目根目录的 `JMComic-Crawler-Python-master` 源码存在。

## 配置说明

编辑 `config.env` 文件进行配置：

- `JM_DOWNLOAD_DIR`: 下载目录路径
- `JM_CLIENT_IMPL`: 客户端类型 (html/api)
- `JM_IMAGE_SUFFIX`: 图片格式后缀
- `JM_PROXY`: 代理设置
- `JM_COOKIES`: 登录cookies（可选）

## 使用方法

### 1. 搜索本子

```
<<<[TOOL_REQUEST]>>>
tool_name:「始」JMCrawl「末」,
command:「始」SearchAlbum「末」,
keyword:「始」恋爱「末」,
page:「始」1「末」,
limit:「始」5「末」
<<<[END_TOOL_REQUEST]>>>
```

### 2. 获取本子信息

```
<<<[TOOL_REQUEST]>>>
tool_name:「始」JMCrawl「末」,
command:「始」GetAlbumInfo「末」,
album_id:「始」422866「末」
<<<[END_TOOL_REQUEST]>>>
```

### 3. 下载本子

```
<<<[TOOL_REQUEST]>>>
tool_name:「始」JMCrawl「末」,
command:「始」DownloadAlbum「末」,
album_id:「始」422866「末」,
download_dir:「始」./downloads/jm「末」,
image_format:「始」.jpg「末」
<<<[END_TOOL_REQUEST]>>>
```

### 4. 下载章节

```
<<<[TOOL_REQUEST]>>>
tool_name:「始」JMCrawl「末」,
command:「始」DownloadPhoto「末」,
photo_id:「始」123456「末」,
download_dir:「始」./downloads/jm「末」,
image_format:「始」.jpg「末」
<<<[END_TOOL_REQUEST]>>>
```

## 支持的命令

| 命令 | 描述 | 必需参数 | 可选参数 |
|------|------|----------|----------|
| `SearchAlbum` | 搜索本子 | `keyword` | `page`, `limit` |
| `GetAlbumInfo` | 获取本子信息 | `album_id` | - |
| `DownloadAlbum` | 下载本子 | `album_id` | `download_dir`, `image_format` |
| `DownloadPhoto` | 下载章节 | `photo_id` | `download_dir`, `image_format` |

## 注意事项

1. **合法使用**: 请遵守相关法律法规，仅用于学习和研究目的
2. **服务器压力**: 请适度使用，避免对服务器造成过大压力
3. **网络环境**: 某些地区可能需要配置代理才能正常访问
4. **登录状态**: 大部分内容无需登录，少数敏感内容需要配置cookies

## 错误处理

插件会返回详细的错误信息，常见问题：

- **网络连接错误**: 检查网络连接和代理设置
- **ID不存在**: 确认本子或章节ID是否正确
- **权限不足**: 某些内容需要登录，请配置cookies
- **依赖缺失**: 确保已安装所有必需的Python库

## 版本信息

- 版本: 1.0.0
- 基于: JMComic-Crawler-Python v2.6.4+
- 兼容: VCP ToolBox 同步插件协议

## 许可证

本插件遵循原项目的开源许可证。请合理合法使用。