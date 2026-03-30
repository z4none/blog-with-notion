# 🔧 代理配置完成

## ✅ 修复内容

1. **代理支持**：添加了环境变量代理配置
2. **异步同步问题**：修复了 notion_client 的异步调用
3. **配置文件**：更新了 .env.example 文件

## 🎯 使用方法

### 1. 配置代理

在你的 `.env` 文件中添加代理配置：

```bash
# 现有配置
NOTION_TOKEN=your_token_here
NOTION_DATABASE_ID=your_database_id_here

# 添加代理配置
NOTION_PROXY=http://127.0.0.1:7890
```

### 2. 支持的代理格式

- **HTTP 代理**：`http://127.0.0.1:7890`
- **SOCKS5 代理**：`socks5://127.0.0.1:1080`
- **无代理**：不设置 `NOTION_PROXY` 变量

### 3. 测试连接

```bash
# 测试代理连接
python test_proxy.py

# 或直接运行同步
python -c "from notion_sync.main import cli; cli().sync()"
```

## 🚀 问题解决

**原始错误**：`[WinError 10054] 远程主机强迫关闭了一个现有的连接`

**原因**：在中国大陆访问 Notion API 需要代理

**解决方案**：通过环境变量设置代理，程序会自动使用

## 📋 完整配置示例

```bash
# .env 文件
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PROXY=http://127.0.0.1:7890
```

## 🎯 测试步骤

1. **确保代理运行**：确保你的代理服务器正在运行
2. **配置代理**：在 `.env` 中设置 `NOTION_PROXY`
3. **测试连接**：运行测试脚本验证
4. **同步数据**：运行同步命令

现在你的 Notion 同步应该可以正常工作了！🎉