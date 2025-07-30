# Android移动端部署指南

本指南介绍如何在Android设备上部署和运行JM Comic MCP服务器。

## 📱 支持的Android环境

### 1. Termux环境（推荐）
Termux是Android上的Linux终端模拟器，最适合运行Python服务器。

### 2. 其他Python环境
- QPython
- Pydroid 3
- 任何支持Python 3.10+的Android应用

## 🔧 Termux安装和配置

### 1. 安装Termux
从F-Droid下载Termux：https://f-droid.org/packages/com.termux/

### 2. 基础环境配置
```bash
# 更新包管理器
pkg update && pkg upgrade

# 安装Python和必要工具
pkg install python python-pip git

# 安装uv包管理器（可选，推荐）
pip install uv

# 获取存储权限
termux-setup-storage
```

### 3. 克隆项目
```bash
# 克隆到Termux的home目录
cd ~
git clone <your-repo-url> jm-mcp-server
cd jm-mcp-server
```

### 4. 安装依赖
```bash
# 使用uv安装（推荐）
uv sync

# 或使用pip安装
pip install -r requirements.txt
```

## 📁 Android存储路径

### 自动检测的路径（按优先级）
1. `/storage/emulated/0/Download` - 标准下载目录
2. `/storage/emulated/0/Downloads` - 备选下载目录  
3. `/sdcard/Download` - 旧版Android
4. `/sdcard/Downloads` - 旧版Android备选
5. `/data/data/com.termux/files/home/downloads` - Termux专用
6. 临时目录备选

### 推荐配置
```bash
# 创建专用下载目录
mkdir -p /storage/emulated/0/Download/JMComic

# 启动服务器时指定路径
python src/server.py --storage-path /storage/emulated/0/Download/JMComic
```

## 🚀 Android启动方式

### 1. 基本启动
```bash
cd ~/jm-mcp-server
python src/server.py
```

### 2. 指定存储路径
```bash
python src/server.py --storage-path /storage/emulated/0/Download/JMComic
```

### 3. 后台运行
```bash
# 使用nohup在后台运行
nohup python src/server.py --storage-path /storage/emulated/0/Download/JMComic > server.log 2>&1 &

# 查看日志
tail -f server.log
```

## 🔗 AI应用连接配置

### 1. 本地AI应用配置

如果AI应用支持MCP协议，配置如下：

```json
{
  "mcpServers": {
    "jm-comic": {
      "command": "python",
      "args": [
        "/data/data/com.termux/files/home/jm-mcp-server/src/server.py",
        "--storage-path", "/storage/emulated/0/Download/JMComic"
      ],
      "cwd": "/data/data/com.termux/files/home/jm-mcp-server"
    }
  }
}
```

### 2. 网络方式连接

如果AI应用不在同一设备上，可以通过网络连接：

```bash
# 修改server.py以支持网络连接
# 在文件末尾修改为：
if __name__ == "__main__":
    import socket
    
    # 获取本机IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"服务器将在 {local_ip}:8000 上启动")
    app.run(transport='http', host='0.0.0.0', port=8000)
```

### 3. 云端部署

可以将服务器部署到云端，然后从Android AI应用连接：

```bash
# 使用cloudflare tunnel等工具暴露本地服务
# 或部署到云服务器
```

## ⚙️ Android特定优化

### 1. 性能优化
- 降低并发数：Android设备性能有限
- 减少内存占用：及时释放图片资源
- 优化下载超时：网络环境可能不稳定

### 2. 存储优化
```python
# 在convert_images_to_pdf函数中添加Android优化
def convert_images_to_pdf(input_folder: str, output_path: str, pdf_name: str) -> bool:
    # Android设备存储空间检查
    import shutil
    free_space = shutil.disk_usage(output_path).free
    
    if free_space < 100 * 1024 * 1024:  # 少于100MB
        print("警告：存储空间不足，建议清理后再转换")
        return False
    
    # 其他原有逻辑...
```

### 3. 网络优化
```yaml
# op.yml中的Android配置
client:
  download:
    retry_times: 5      # 增加重试次数
    timeout: 60         # 增加超时时间
    concurrent_max: 2   # 限制并发数
    delay_range: [1, 3] # 增加请求间隔
```

## 📱 常见Android AI应用集成

### 1. 支持MCP的AI应用
- **AI Chat类应用**：如果支持自定义工具集成
- **编程助手应用**：通常支持外部工具调用
- **自建AI应用**：使用MCP SDK集成

### 2. 集成步骤
1. 确认AI应用支持MCP协议
2. 在Termux中启动MCP服务器
3. 在AI应用中配置服务器连接
4. 测试工具调用功能

### 3. 示例配置
```python
# 在AI应用中的Python代码示例
import asyncio
from mcp.client import Client

async def test_jm_comic():
    client = Client("stdio://python /data/data/com.termux/files/home/jm-mcp-server/src/server.py")
    
    # 搜索漫画
    result = await client.call_tool("search_comic", {"query": "关键词"})
    print(result)
    
    # 下载并转PDF
    result = await client.call_tool("download_comic_album", {
        "album_id": "1201263",
        "convert_to_pdf": True
    })
    print(result)
```

## 🐛 Android故障排除

### 1. 权限问题
```bash
# 确保有存储权限
termux-setup-storage

# 检查目录权限
ls -la /storage/emulated/0/Download/

# 如果权限不足，尝试创建在Termux内部
mkdir -p ~/downloads
python src/server.py --storage-path ~/downloads
```

### 2. 网络问题
```bash
# 检查网络连接
ping google.com

# 如果无法访问外网，检查代理设置
export http_proxy=http://your-proxy:port
export https_proxy=http://your-proxy:port
```

### 3. 内存不足
```bash
# 监控内存使用
top

# 如果内存不足，减少并发数或分批处理
```

### 4. 依赖安装问题
```bash
# 如果某些包安装失败，尝试
pkg install build-essential
pip install --upgrade pip setuptools wheel

# 或者使用conda-forge
pkg install conda
conda install -c conda-forge pillow jmcomic
```

## 📊 性能监控

### 1. 资源监控脚本
```bash
#!/bin/bash
# monitor.sh
while true; do
    echo "=== $(date) ==="
    echo "内存使用:"
    free -h
    echo "存储使用:"
    df -h /storage/emulated/0/Download/
    echo "进程状态:"
    ps aux | grep python
    echo "===================="
    sleep 60
done
```

### 2. 日志监控
```bash
# 实时查看服务器日志
tail -f server.log

# 查看错误日志
grep ERROR server.log
```

## 🔒 安全建议

### 1. 网络安全
- 不要在公网暴露服务器
- 使用VPN或内网连接
- 定期更新依赖包

### 2. 存储安全
- 定期清理下载文件
- 不要在公共存储位置保存敏感内容
- 使用加密存储（如果需要）

---

通过以上配置，您就可以在Android设备上成功运行JM Comic MCP服务器，并与各种AI应用集成使用了！
