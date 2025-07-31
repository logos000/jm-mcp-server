# JM Comic MCP Server

一个基于 Model Context Protocol (MCP) 的 JM 漫画下载和 PDF 转换服务器，支持搜索、下载漫画并自动转换为 PDF 格式。

## 🛠️ 安装步骤

### 1. 下载项目
```bash
git clone https://github.com/logos000/jm-mcp-server.git
cd jm-mcp-server
```

### 2. 安装依赖
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
        "--directory", "E:/YourClonePath/jm-mcp-server",
        "run", "src/server.py",
        "--storage-path", "C:/Users/YourName/Downloads"
      ]
    }
  }
}
```

## 📚 可用工具

### 1. search_comic
搜索漫画内容，支持分类、时间段、排序等高级筛选

### 2. get_album_details
获取指定专辑的详细信息（标题、作者、标签等）

### 3. download_comic_album
下载漫画专辑并可选择自动转换为PDF

### 4. convert_album_to_pdf_tool
手动将已下载的专辑转换为PDF格式

### 5. get_ranking_list
获取周榜、月榜或总榜排行榜

### 6. filter_comics_by_category
按分类、时间段和排序方式筛选漫画

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

## 致谢

本项目基于以下开源项目构建，感谢这些优秀的开发者：

- **[JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)** - 提供了核心的JM漫画爬取功能
- **[image2pdf](https://github.com/salikx/image2pdf)** - 提供了图片到PDF转换的灵感和参考

感谢开源社区的贡献！

## 许可证

本项目使用 MIT 许可证，仅供学习和研究使用，请遵守相关法律法规。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

---

**注意**: 请确保您有权下载和使用相关内容，并遵守版权法规。
