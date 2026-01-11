#!/usr/bin/env python3
"""
Gemini Google Search Example

This example demonstrates how to use the GeminiSearch class to perform
web searches using Google Gemini's built-in Google Search grounding feature.

Before running this example, make sure to:
1. Install the required dependencies: pip install toolregistry-hub
2. Set your GEMINI_API_KEY environment variable:
   export GEMINI_API_KEY="your-api-key-here"

You can get a free API key from: https://aistudio.google.com/
"""

import os
import sys

# Add parent directory to path to import toolregistry_hub
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from toolregistry_hub.websearch import GeminiSearch


def main():
    """Main function to demonstrate Gemini search."""
    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("错误: 请设置 GEMINI_API_KEY 环境变量")
        print("获取免费 API 密钥: https://aistudio.google.com/")
        return

    print("=" * 60)
    print("Gemini Google Search 示例")
    print("=" * 60)
    print()

    # Initialize search with rate limiting
    print("初始化 Gemini 搜索客户端...")
    search = GeminiSearch(
        api_keys=api_key,
        rate_limit_delay=1.0,  # 1 second delay between requests
    )
    print("✓ 初始化成功")
    print()

    # Example 1: Basic search
    print("-" * 60)
    print("示例 1: 基本搜索")
    print("-" * 60)
    query1 = "Python 最新特性"
    print(f"搜索查询: {query1}")
    print()

    try:
        results1 = search.search(query1, max_results=3)

        if results1:
            print(f"找到 {len(results1)} 个结果:\n")
            for i, result in enumerate(results1, 1):
                print(f"{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   内容预览: {result.content[:200]}...")
                print(f"   评分: {result.score:.3f}")
                print()
        else:
            print("未找到结果")
    except Exception as e:
        print(f"搜索失败: {e}")

    # Example 2: Technical search
    print("-" * 60)
    print("示例 2: 技术搜索")
    print("-" * 60)
    query2 = "machine learning best practices 2024"
    print(f"搜索查询: {query2}")
    print()

    try:
        results2 = search.search(query2, max_results=5, timeout=15.0)

        if results2:
            print(f"找到 {len(results2)} 个结果:\n")
            for i, result in enumerate(results2, 1):
                print(f"{i}. {result.title}")
                print(f"   URL: {result.url}")
                if result.url:  # Only show preview if URL exists
                    print(f"   内容预览: {result.content[:150]}...")
                else:
                    print(f"   综合答案: {result.content[:300]}...")
                print()
        else:
            print("未找到结果")
    except Exception as e:
        print(f"搜索失败: {e}")

    print("=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()