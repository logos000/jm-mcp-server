# JM Comic MCP Server

一个基于 Model Context Protocol (MCP) 的 JM 漫画下载和 PDF 转换服务器，支持搜索、下载漫画并自动转换为 PDF 格式。

## ✨ 功能特性

- 🔍 **漫画搜索**：支持关键词搜索漫画内容
- 📖 **专辑详情**：获取漫画的详细信息（标题、作者、标签等）
- 📊 **排行榜**：获取周榜、月榜和总榜排行榜
- 📥 **智能下载**：自动下载漫画图片到指定目录
- 📄 **自动PDF转换**：下载完成后自动将图片转换为PDF
- 🎯 **批量转换**：支持批量将已下载的漫画转换为PDF
- ⚙️ **灵活配置**：支持命令行参数自定义存储路径
- 🔧 **智能匹配**：通过专辑标题智能匹配下载目录

## 🛠️ 安装依赖

确保您已安装 Python 3.10+ 和 uv 包管理器。



### 手动安装依赖(应该不需要)
```bash
uv pip install e .
```


## 🔧 配置文件

服务器使用 `op.yml` 配置文件：

```yaml
dir_rule:
  base_dir: C:/Users/YourName/Downloads
```

当使用 `--storage-path` 参数时，配置文件会自动更新。

## 🔗 MCP 客户端配置



### Windows 配置示例

```json
{
  "mcpServers": {
    "jm-comic": {
      "command": "uv",
      "args": [
        "--directory", "E:/AAProgramming/mcp_server/jm-mcp-server",
        "run", "src/server.py",
        "--storage-path", "C:/Users/YourName/Downloads"
      ]
    }
  }
}
```

## 📚 可用工具

### 1. search_comic
搜索漫画内容

**参数：**
- `query` (string): 搜索关键词
- `page` (int, 可选): 页码，默认为 1

**示例：**
```
search_comic("关键词")
```

### 2. get_album_details
获取专辑详细信息

**参数：**
- `album_id` (string): 专辑ID

**示例：**
```
get_album_details("1201263")
```

### 3. download_comic_album
下载漫画专辑并转换为PDF

**参数：**
- `album_id` (string): 专辑ID
- `convert_to_pdf` (bool, 可选): 是否转换为PDF，默认为 true

**示例：**
```
download_comic_album("1201263")
download_comic_album("1201263", false)  # 只下载不转换
```

### 4. convert_album_to_pdf_tool
手动转换已下载的专辑为PDF

**参数：**
- `album_id` (string): 专辑ID
- `album_dir` (string, 可选): 自定义专辑目录路径

**示例：**
```
convert_album_to_pdf_tool("1201263")
```

### 5. batch_convert_to_pdf
批量转换目录下的所有专辑为PDF

**参数：**
- `base_directory` (string, 可选): 基础目录，默认使用配置的下载目录

**示例：**
```
batch_convert_to_pdf()
batch_convert_to_pdf("/custom/path")
```

### 6. get_ranking_list
获取排行榜

**参数：**
- `period` (string, 可选): 时间段，可选值：'week', 'month', 'all'，默认为 'week'

**示例：**
```
get_ranking_list()          # 周榜
get_ranking_list("month")   # 月榜
get_ranking_list("all")     # 总榜
```

## 📂 目录结构

```
jm-mcp-server/
├── src/
│   └── server.py           # 主服务器文件
├── op.yml                  # 配置文件
├── pyproject.toml          # 项目配置
├── README.md               # 项目说明
└── uv.lock                 # 依赖锁定文件
```

## 🔍 工作原理

### 下载流程
1. 调用 `download_comic_album` 工具
2. 获取专辑详情和标题
3. 下载图片到 `{base_dir}/{album_title}/` 目录
4. 自动检测下载完成
5. 将图片转换为PDF并保存到 `{base_dir}/{album_title}.pdf`

### 目录匹配策略
服务器使用多层匹配策略找到正确的下载目录：

1. **完全匹配**：专辑标题完全匹配目录名
2. **部分匹配**：专辑标题包含在目录名中
3. **ID匹配**：目录名包含专辑ID
4. **时间匹配**：最近30分钟内创建的包含图片的目录

### PDF转换特性
- 自动跳过已存在的PDF文件
- 支持多种图片格式：JPG, PNG, WebP, BMP
- 自动转换为RGB模式确保兼容性
- 智能跳过损坏的图片文件
- 文件大小优化（质量85%压缩）

## 🐛 故障排除

### 常见问题

**Q: 服务器启动时提示 "unrecognized arguments"？**
A: 这是正常现象，服务器使用了 `parse_known_args()` 来兼容 MCP 开发模式。

**Q: 下载后没有自动转换PDF？**
A: 检查以下几点：
- 确保下载目录存在且可访问
- 确认 `convert_to_pdf` 参数为 true
- 查看控制台输出的调试信息

**Q: 无法找到下载的专辑目录？**
A: 服务器会自动搜索匹配的目录，包括：
- 使用专辑标题匹配
- 使用专辑ID匹配  
- 检查最近创建的目录

**Q: PDF转换失败？**
A: 检查：
- 目录中是否包含有效的图片文件
- 图片文件是否损坏
- 磁盘空间是否充足

### 调试信息

启动服务器后，控制台会显示详细的调试信息：
```
[下载] 开始下载专辑 1201263
[调试] 下载目录: C:/Users/YourName/Downloads
[调试] 专辑标题: 示例专辑标题
[完成] 专辑 1201263 下载完成
[转换] 开始转换专辑 1201263 为PDF
[成功] 专辑 1201263 PDF转换完成
```

## 📝 开发说明

### 项目依赖
- `jmcomic`: JM漫画API库
- `Pillow`: 图像处理和PDF转换
- `pyyaml`: YAML配置文件处理
- `mcp`: Model Context Protocol框架

### 核心功能模块
- **参数解析**: 命令行参数处理和配置文件更新
- **漫画API**: 搜索、获取详情、下载功能
- **PDF转换**: 图片到PDF的转换逻辑
- **目录管理**: 智能目录检测和匹配
- **异步处理**: 后台下载和转换任务

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

---

**注意**: 请确保您有权下载和使用相关内容，并遵守版权法规。
