# ToolRegistry-Hub 工具选择器使用指南

## 概述

工具选择器是一个独立的 Web 界面，允许您动态控制 ToolRegistry-Hub 主服务器中各种工具的启用/禁用状态。通过简单的 toggle 开关，您可以实时控制哪些 API 端点可用，而无需重启服务器。

## 功能特性

- 🔍 **自动发现工具**：基于现有路由结构自动发现所有可用工具
- 🎛️ **实时控制**：通过 toggle 开关即时启用/禁用工具
- 🔄 **热重载**：支持重新加载服务器以发现新工具
- 💾 **配置持久化**：工具状态自动保存，重启后保持
- 🌐 **独立运行**：在不同端口运行，与主服务器完全隔离
- 📊 **状态监控**：实时显示服务器状态和工具统计

## 快速开始

### 1. 启动主服务器

```bash
# 激活 conda 环境
conda activate tr_h_3.10

# 启动主 API 服务器（端口 8000）
toolregistry-server --mode openapi --port 8000
```

### 2. 启动选择器服务器

```bash
# 在新的终端窗口中启动选择器（端口 8001）
toolregistry-server --mode selector --port 8001
```

### 3. 访问选择器界面

打开浏览器访问：http://localhost:8001

## 界面说明

### 主界面布局

```
┌─────────────────────────────────────────────────────────┐
│ 🛠️ ToolRegistry-Hub 工具选择器                          │
│                                    [🔄 重新加载] [🔍 刷新] │
├─────────────────────────────────────────────────────────┤
│ 状态: 正在运行 | 工具数: 5 | 已启用: 4 | 服务器状态: ● │
├─────────────────────────────────────────────────────────┤
│ 工具名称 │ API前缀 │ 标签 │ 端点数 │ 模块 │ 状态 │ 操作 │
├─────────────────────────────────────────────────────────┤
│ Calculator │ /calc │ calculator │ 3 │ calculator │ ✅启用 │ [●] │
│ DateTime   │ /time │ datetime   │ 2 │ datetime   │ ✅启用 │ [●] │
│ Think      │ /     │ think      │ 1 │ think      │ ❌禁用 │ [○] │
│ ...        │ ...   │ ...        │...│ ...        │ ...    │ ... │
└─────────────────────────────────────────────────────────┘
```

### 控制按钮

- **🔄 重新加载服务器**：重新启动主服务器的工具发现机制
- **🔍 刷新工具列表**：刷新选择器界面的工具列表
- **Toggle 开关**：点击切换工具的启用/禁用状态

### 状态指示器

- **绿色圆点 (●)**：服务器在线
- **红色圆点 (●)**：服务器离线
- **✅ 启用**：工具当前可用
- **❌ 禁用**：工具当前不可用

## 发现的工具

当前系统发现了以下工具：

### 1. Calculator (计算器)

- **前缀**: `/calc`
- **端点**: 3 个
  - `POST /calc/evaluate` - 计算数学表达式
  - `POST /calc/help` - 获取函数帮助
  - `POST /calc/allowed_fns` - 列出允许的函数

### 2. DateTime Tools (时间工具)

- **前缀**: `/time`
- **端点**: 2 个
  - `POST /time/now` - 获取当前时间
  - `POST /time/convert` - 时区转换

### 3. Think Tool (思考工具)

- **前缀**: `/`
- **端点**: 1 个
  - `POST /think` - 处理思考内容

### 4. Fetch Tool (抓取工具)

- **前缀**: `/`
- **端点**: 1 个
  - `POST /fetch/webpage` - 抓取网页内容

### 5. WebSearch Tools (网络搜索)

- **前缀**: `/web`
- **端点**: 1 个（Bing 搜索）
  - `POST /web/search` - 网络搜索

## 使用场景

### 场景 1：开发调试

在开发过程中，您可能只想启用特定的工具进行测试：

1. 禁用所有工具
2. 只启用正在开发的工具
3. 测试完成后重新启用其他工具

### 场景 2：性能优化

对于生产环境，您可能想要：

1. 禁用不常用的工具以减少内存占用
2. 只启用核心功能
3. 根据负载情况动态调整

### 场景 3：安全控制

在某些环境中，您可能需要：

1. 禁用具有安全风险的工具
2. 只启用经过审核的功能
3. 临时禁用有问题的工具

## 配置文件

工具状态保存在 `config/tools_config.json` 文件中：

```json
{
  "tools": {
    "calc_b58abfaf": {
      "id": "calc_b58abfaf",
      "name": "Calculator",
      "prefix": "/calc",
      "enabled": true,
      "description": "Mathematical calculator tool",
      "tags": ["calculator"],
      "endpoints": [...],
      "module_name": "toolregistry_hub.server.routes.calculator"
    }
  },
  "last_updated": "2025-11-30T00:08:52.753000",
  "version": "1.0.0"
}
```

## 高级用法

### 命令行选项

```bash
# 自定义端口
toolregistry-server --mode selector --port 8002

# 指定主服务器地址
toolregistry-server --mode selector --main-server-url http://localhost:9000

# 自定义主机
toolregistry-server --mode selector --host 127.0.0.1 --port 8001
```

### 键盘快捷键

- `Ctrl+R` / `Cmd+R`：刷新工具列表
- `Ctrl+Shift+R` / `Cmd+Shift+R`：重新加载服务器

### API 端点

选择器服务器提供以下 API 端点：

- `GET /api/tools` - 获取所有工具信息
- `POST /api/tools/{tool_id}/toggle` - 切换工具状态
- `POST /api/server/reload` - 重新加载服务器
- `GET /api/tools/status` - 获取工具状态
- `GET /health` - 健康检查

## 故障排除

### 问题 1：选择器无法连接到主服务器

**症状**：服务器状态显示离线，toggle 操作失败

**解决方案**：

1. 确认主服务器正在运行
2. 检查端口是否正确（默认 8000）
3. 检查防火墙设置

### 问题 2：工具列表为空

**症状**：界面显示"未发现任何工具"

**解决方案**：

1. 点击"重新加载服务器"按钮
2. 检查主服务器日志
3. 确认路由模块正确安装

### 问题 3：Toggle 开关不响应

**症状**：点击开关后状态不变

**解决方案**：

1. 检查浏览器控制台错误
2. 刷新页面重试
3. 检查网络连接

### 问题 4：配置不持久化

**症状**：重启后工具状态重置

**解决方案**：

1. 检查 `config/` 目录权限
2. 确认磁盘空间充足
3. 查看服务器日志错误信息

## 技术架构

### 组件关系

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Selector      │◄──────────────►│   Main Server   │
│   (Port 8001)   │                │   (Port 8000)   │
└─────────────────┘                └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│   Static Files  │                │ Dynamic Router  │
│   (HTML/CSS/JS) │                │   Manager       │
└─────────────────┘                └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│   Route         │                │   Tool Routes   │
│   Inspector     │                │   (calc/time/   │
└─────────────────┘                │    think/etc)   │
                                   └─────────────────┘
```

### 数据流

1. **工具发现**：Route Inspector 扫描 routes 目录
2. **状态管理**：Dynamic Router Manager 控制路由启用
3. **界面交互**：Selector App 提供 Web 界面
4. **配置持久化**：状态保存到 JSON 文件

## 扩展开发

如果您想要扩展选择器功能，可以：

1. **添加新的 API 端点**：在 `selector/app.py` 中添加路由
2. **自定义界面**：修改 `static/` 目录下的文件
3. **扩展工具检测**：修改 `route_inspector.py` 的逻辑
4. **添加新功能**：在 `dynamic_router.py` 中实现

## 支持

如果您遇到问题或有建议，请：

1. 查看服务器日志获取详细错误信息
2. 运行测试脚本验证系统状态：`python test_selector_system.py`
3. 检查配置文件是否正确
4. 确认所有依赖包已正确安装

---

**享受使用 ToolRegistry-Hub 工具选择器！** 🎉
