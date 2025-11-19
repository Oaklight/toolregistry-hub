---
title: 网页获取工具
summary: 从URL获取网页内容
description: Fetch类提供从URL获取网页内容的功能，支持超时和代理设置。
keywords: 网页, 获取, 内容, url, http
author: ToolRegistry Hub 团队
---

# 网页获取工具

网页内容获取工具提供了从 URL 获取网页内容的功能。

## 概览

`Fetch` 类专为从网页检索内容而设计。它支持：

- HTTP/HTTPS URL 获取
- 可配置的超时设置
- 代理支持
- 内容提取和清理
- 网络问题的错误处理

## 类参考

### Fetch

提供网页内容获取功能的类。

#### 方法

##### `fetch_content(url: str, timeout: float = 10.0, proxy: Optional[str] = None) -> str`

从 URL 获取网页内容。

**参数：**
- `url` (str): 要获取内容的 URL
- `timeout` (float, 可选): 请求超时时间（秒）。默认为 10.0
- `proxy` (Optional[str], 可选): 要使用的代理服务器。默认为 None

**返回值：**
- `str`: 从网页提取的内容

**异常：**
- `requests.RequestException`: 如果请求失败
- `ValueError`: 如果 URL 无效

**示例：**
```python
from toolregistry_hub import Fetch

# 获取网页内容
content = Fetch.fetch_content("https://www.example.com")
print(f"网页内容长度: {len(content)} 字符")
print(f"网页内容预览: {content[:200]}...")
```

## 使用场景

### 基本网页内容获取

```python
from toolregistry_hub import Fetch

# 从网站获取内容
try:
    content = Fetch.fetch_content("https://httpbin.org/html")
    print(f"成功获取 {len(content)} 字符")
    print("内容预览:", content[:100])
except Exception as e:
    print(f"获取内容失败: {e}")
```

### 使用自定义超时

```python
from toolregistry_hub import Fetch

# 使用自定义超时获取
try:
    content = Fetch.fetch_content(
        "https://httpbin.org/delay/5", 
        timeout=10.0
    )
    print("内容获取成功")
except Exception as e:
    print(f"请求超时或失败: {e}")
```

### 使用代理

```python
from toolregistry_hub import Fetch

# 通过代理获取
try:
    content = Fetch.fetch_content(
        "https://httpbin.org/ip",
        proxy="http://proxy.example.com:8080"
    )
    print("通过代理获取的内容:", content)
except Exception as e:
    print(f"代理请求失败: {e}")
```

### 内容分析

```python
from toolregistry_hub import Fetch
import re

# 获取并分析内容
def analyze_webpage(url):
    try:
        content = Fetch.fetch_content(url)
        
        # 基本内容分析
        word_count = len(content.split())
        char_count = len(content)
        
        # 提取潜在的电子邮件地址
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        
        # 提取潜在的 URL
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'emails_found': len(emails),
            'urls_found': len(urls),
            'content_preview': content[:200]
        }
    except Exception as e:
        return {'error': str(e)}

# 分析网页
result = analyze_webpage("https://www.example.com")
print("分析结果:", result)
```

## 错误处理

`fetch_content` 方法可能引发各种异常。以下是处理方法：

```python
from toolregistry_hub import Fetch
import requests

def safe_fetch(url, timeout=10.0, proxy=None):
    try:
        content = Fetch.fetch_content(url, timeout=timeout, proxy=proxy)
        return {'success': True, 'content': content}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': '请求超时'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': '连接失败'}
    except requests.exceptions.HTTPError as e:
        return {'success': False, 'error': f'HTTP 错误: {e}'}
    except ValueError as e:
        return {'success': False, 'error': f'无效 URL: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'意外错误: {e}'}

# 安全获取并处理错误
result = safe_fetch("https://www.example.com")
if result['success']:
    print(f"内容已获取: {len(result['content'])} 字符")
else:
    print(f"获取失败: {result['error']}")
```

## 最佳实践

1. **设置适当的超时**：使用合理的超时值以避免请求挂起
2. **处理异常**：始终将获取调用包装在 try-except 块中
3. **尊重速率限制**：不要在短时间内发出太多请求
4. **检查内容大小**：注意可能消耗内存的大内容
5. **验证 URL**：在获取前确保 URL 格式正确

## 安全考虑

- 从不受信任的来源获取内容时要谨慎
- 在处理前验证和清理任何内容
- 尽可能考虑使用 HTTPS URL
- 使用代理时要注意潜在的安全风险

## 导航

- [返回首页](index.md)
- [思考工具](think_tool.md)
- [其他工具](other_tools.md)
- [计算器工具](calculator.md)