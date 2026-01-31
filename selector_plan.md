# 工具选择器系统设计方案（修订版）

## 项目概述

为 ToolRegistry-Hub 添加一个独立的工具选择器系统，允许用户通过简单的 HTML 界面动态启用/禁用各种工具的 API endpoints。

**核心原则：**

- 不修改现有 routes 结构
- 基于现有的 `discover_routers()` 机制动态发现工具
- selector 组件独立运行在不同端口
- 提供 reload 功能重新加载工具服务器

## 当前工具模块分析

从代码分析中发现的主要工具模块：

1. **Calculator** (`/calc`) - 数学计算工具
2. **DateTime Tools** (`/time`) - 时间处理工具
3. **Think Tool** (`/think`) - 思考工具
4. **Fetch Tool** (`/fetch`) - 网页抓取工具
5. **WebSearch Tools** (`/web`) - 网络搜索工具

## 修订后的架构设计

### 系统架构图

```mermaid
graph TB
    A[Selector 服务器<br/>端口 8001] --> B[路由发现器]
    A --> C[HTML 界面]
    A --> D[状态管理 API]

    B --> E[discover_routers()]
    E --> F[现有 routes 结构]

    D --> G[主 FastAPI 服务器<br/>端口 8000]
    G --> H[动态路由管理器]
    H --> I[启用的路由池]

    C --> J[工具状态表格]
    J --> K[Toggle 开关]
    J --> L[Reload 按钮]

    subgraph "现有 Routes 结构（不变）"
        M[routes/calculator.py]
        N[routes/datetime_tools.py]
        O[routes/think.py]
        P[routes/fetch.py]
        Q[routes/websearch/]
    end

    F --> M
    F --> N
    F --> O
    F --> P
    F --> Q
```

### 新增文件结构

```
src/toolregistry_hub/server/
├── selector/                        # 新增：selector 组件
│   ├── __init__.py
│   ├── app.py                       # selector 服务器应用
│   ├── models.py                    # 数据模型
│   ├── route_inspector.py           # 路由检查器
│   ├── static/                      # 静态文件目录
│   │   ├── index.html              # 主界面
│   │   ├── style.css               # 样式文件
│   │   └── script.js               # 前端逻辑
│   └── api/                         # selector API
│       ├── __init__.py
│       ├── tools.py                # 工具管理 API
│       └── server.py               # 服务器控制 API
├── dynamic_router.py                # 新增：动态路由管理器
├── server_openapi.py                # 修改：支持动态路由
└── cli.py                          # 修改：添加 selector 模式
```

## 核心组件设计

### 1. 路由检查器（Route Inspector）

```python
from typing import List, Dict, Any
from fastapi import APIRouter
from ..routes import discover_routers

class RouteInspector:
    """路由检查器 - 基于现有的 discover_routers() 发现工具"""

    def __init__(self):
        self.discovered_routers: List[APIRouter] = []
        self.tool_info: Dict[str, Any] = {}

    def discover_tools(self) -> Dict[str, Any]:
        """发现所有可用工具"""
        self.discovered_routers = discover_routers()
        self.tool_info = self._extract_tool_info()
        return self.tool_info

    def _extract_tool_info(self) -> Dict[str, Any]:
        """从路由中提取工具信息"""
        tools = {}
        for router in self.discovered_routers:
            tool_id = self._get_tool_id(router)
            tools[tool_id] = {
                'id': tool_id,
                'name': self._get_tool_name(router),
                'prefix': router.prefix or '/',
                'tags': list(router.tags) if router.tags else [],
                'endpoints': self._extract_endpoints(router),
                'enabled': True  # 默认启用
            }
        return tools

    def _extract_endpoints(self, router: APIRouter) -> List[Dict]:
        """提取路由的端点信息"""
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                endpoints.append({
                    'path': route.path,
                    'methods': list(route.methods),
                    'name': getattr(route, 'name', ''),
                    'summary': getattr(route, 'summary', ''),
                })
        return endpoints
```

### 2. 动态路由管理器

```python
from typing import Dict, Set
from fastapi import FastAPI, APIRouter

class DynamicRouterManager:
    """动态路由管理器 - 控制路由的启用/禁用"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.all_routers: Dict[str, APIRouter] = {}
        self.enabled_tools: Set[str] = set()
        self.route_inspector = RouteInspector()

    def initialize(self):
        """初始化 - 发现并注册所有路由"""
        tools = self.route_inspector.discover_tools()
        for tool_id, tool_info in tools.items():
            router = self._find_router_by_id(tool_id)
            if router:
                self.all_routers[tool_id] = router
                self.enabled_tools.add(tool_id)
                self.app.include_router(router)

    def enable_tool(self, tool_id: str) -> bool:
        """启用工具"""
        if tool_id in self.all_routers and tool_id not in self.enabled_tools:
            router = self.all_routers[tool_id]
            self.app.include_router(router)
            self.enabled_tools.add(tool_id)
            return True
        return False

    def disable_tool(self, tool_id: str) -> bool:
        """禁用工具"""
        if tool_id in self.enabled_tools:
            # FastAPI 不支持直接移除路由，需要重建应用
            self.enabled_tools.discard(tool_id)
            self._rebuild_app_routes()
            return True
        return False

    def reload_tools(self) -> Dict[str, Any]:
        """重新加载所有工具"""
        # 重新发现路由
        tools = self.route_inspector.discover_tools()
        # 更新路由注册
        self._rebuild_app_routes()
        return tools

    def _rebuild_app_routes(self):
        """重建应用路由（仅包含启用的工具）"""
        # 清除现有路由
        self.app.router.routes = [
            route for route in self.app.router.routes
            if not hasattr(route, 'tags') or not route.tags
        ]

        # 重新添加启用的路由
        for tool_id in self.enabled_tools:
            if tool_id in self.all_routers:
                self.app.include_router(self.all_routers[tool_id])
```

### 3. Selector 服务器应用

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
from pathlib import Path

class SelectorApp:
    """Selector 服务器应用"""

    def __init__(self, main_server_url: str = "http://localhost:8000"):
        self.app = FastAPI(title="Tool Selector", version="1.0.0")
        self.main_server_url = main_server_url
        self.route_inspector = RouteInspector()
        self.setup_routes()
        self.setup_static_files()

    def setup_static_files(self):
        """设置静态文件服务"""
        static_path = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=static_path), name="static")

    def setup_routes(self):
        """设置 API 路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """主页面"""
            static_path = Path(__file__).parent / "static" / "index.html"
            return HTMLResponse(content=static_path.read_text(), status_code=200)

        @self.app.get("/api/tools")
        async def get_tools():
            """获取所有工具信息"""
            return self.route_inspector.discover_tools()

        @self.app.post("/api/tools/{tool_id}/toggle")
        async def toggle_tool(tool_id: str):
            """切换工具启用状态"""
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.main_server_url}/internal/tools/{tool_id}/toggle"
                )
                return response.json()

        @self.app.post("/api/server/reload")
        async def reload_server():
            """重新加载主服务器"""
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.main_server_url}/internal/server/reload"
                )
                return response.json()

        @self.app.get("/api/tools/status")
        async def get_tools_status():
            """获取工具状态"""
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.main_server_url}/internal/tools/status"
                )
                return response.json()
```

### 4. HTML 界面设计

#### index.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>工具选择器</title>
    <link rel="stylesheet" href="/static/style.css" />
  </head>
  <body>
    <div class="container">
      <header>
        <h1>ToolRegistry-Hub 工具选择器</h1>
        <div class="controls">
          <button id="reload-btn" class="btn btn-primary">
            🔄 重新加载服务器
          </button>
          <button id="refresh-btn" class="btn btn-secondary">
            🔍 刷新工具列表
          </button>
        </div>
      </header>

      <main>
        <div class="status-bar">
          <span id="status-text">正在加载...</span>
          <span id="server-status" class="status-indicator">●</span>
        </div>

        <table id="tools-table" class="tools-table">
          <thead>
            <tr>
              <th>工具名称</th>
              <th>前缀</th>
              <th>标签</th>
              <th>端点数</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody id="tools-tbody">
            <!-- 动态生成 -->
          </tbody>
        </table>
      </main>
    </div>

    <script src="/static/script.js"></script>
  </body>
</html>
```

#### style.css

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn:hover {
  opacity: 0.9;
}

.status-bar {
  background: white;
  padding: 10px 20px;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-indicator {
  font-size: 20px;
}

.status-indicator.online {
  color: #28a745;
}

.status-indicator.offline {
  color: #dc3545;
}

.tools-table {
  width: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tools-table th,
.tools-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.tools-table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #28a745;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.tag {
  display: inline-block;
  background-color: #e9ecef;
  color: #495057;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  margin-right: 4px;
}

.status-enabled {
  color: #28a745;
  font-weight: bold;
}

.status-disabled {
  color: #dc3545;
  font-weight: bold;
}
```

#### script.js

```javascript
class ToolSelector {
  constructor() {
    this.tools = {};
    this.init();
  }

  async init() {
    await this.loadTools();
    this.setupEventListeners();
    this.startStatusPolling();
  }

  async loadTools() {
    try {
      const response = await fetch("/api/tools");
      this.tools = await response.json();
      this.renderToolsTable();
      this.updateStatus("工具列表已加载");
    } catch (error) {
      console.error("加载工具失败:", error);
      this.updateStatus("加载工具失败", "error");
    }
  }

  renderToolsTable() {
    const tbody = document.getElementById("tools-tbody");
    tbody.innerHTML = "";

    Object.values(this.tools).forEach((tool) => {
      const row = this.createToolRow(tool);
      tbody.appendChild(row);
    });
  }

  createToolRow(tool) {
    const row = document.createElement("tr");
    row.innerHTML = `
            <td>${tool.name}</td>
            <td><code>${tool.prefix}</code></td>
            <td>${tool.tags
              .map((tag) => `<span class="tag">${tag}</span>`)
              .join("")}</td>
            <td>${tool.endpoints.length}</td>
            <td>
                <span class="status-${tool.enabled ? "enabled" : "disabled"}">
                    ${tool.enabled ? "启用" : "禁用"}
                </span>
            </td>
            <td>
                <label class="toggle-switch">
                    <input type="checkbox" ${tool.enabled ? "checked" : ""} 
                           onchange="toolSelector.toggleTool('${
                             tool.id
                           }', this.checked)">
                    <span class="slider"></span>
                </label>
            </td>
        `;
    return row;
  }

  async toggleTool(toolId, enabled) {
    try {
      const response = await fetch(`/api/tools/${toolId}/toggle`, {
        method: "POST",
      });
      const result = await response.json();

      if (result.success) {
        this.tools[toolId].enabled = enabled;
        this.updateStatus(`工具 ${toolId} 已${enabled ? "启用" : "禁用"}`);
      } else {
        this.updateStatus(`切换工具 ${toolId} 失败`, "error");
        // 恢复开关状态
        this.renderToolsTable();
      }
    } catch (error) {
      console.error("切换工具失败:", error);
      this.updateStatus("切换工具失败", "error");
      this.renderToolsTable();
    }
  }

  async reloadServer() {
    this.updateStatus("正在重新加载服务器...");
    try {
      const response = await fetch("/api/server/reload", {
        method: "POST",
      });
      const result = await response.json();

      if (result.success) {
        this.updateStatus("服务器重新加载成功");
        await this.loadTools();
      } else {
        this.updateStatus("服务器重新加载失败", "error");
      }
    } catch (error) {
      console.error("重新加载服务器失败:", error);
      this.updateStatus("重新加载服务器失败", "error");
    }
  }

  setupEventListeners() {
    document.getElementById("reload-btn").addEventListener("click", () => {
      this.reloadServer();
    });

    document.getElementById("refresh-btn").addEventListener("click", () => {
      this.loadTools();
    });
  }

  async startStatusPolling() {
    setInterval(async () => {
      try {
        const response = await fetch("/api/tools/status");
        const status = await response.json();
        this.updateServerStatus(true);
      } catch (error) {
        this.updateServerStatus(false);
      }
    }, 5000);
  }

  updateServerStatus(online) {
    const indicator = document.getElementById("server-status");
    indicator.className = `status-indicator ${online ? "online" : "offline"}`;
  }

  updateStatus(message, type = "info") {
    const statusText = document.getElementById("status-text");
    statusText.textContent = message;
    statusText.className = type === "error" ? "error" : "";
  }
}

// 初始化
const toolSelector = new ToolSelector();
```

## 实现优势

1. **零侵入性**：完全不修改现有 routes 结构
2. **动态发现**：基于现有的 `discover_routers()` 机制
3. **独立运行**：selector 在不同端口运行
4. **实时控制**：toggle 开关即时生效
5. **重载功能**：reload 按钮重新加载工具服务器
6. **状态持久化**：配置保存到文件
7. **简洁界面**：HTML 表格 + CSS + JavaScript

## 下一步实施

1. 创建 selector 组件目录结构
2. 实现路由检查器和动态路由管理器
3. 开发 selector 服务器应用
4. 创建 HTML/CSS/JS 静态文件
5. 修改主服务器支持内部 API
6. 更新 CLI 支持 selector 模式
7. 测试完整功能
