"""Example usage of the browser_use module with user-defined URLs."""

import asyncio
import os
import sys

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from toolregistry_hub.browser_use import (
    BrowserFetch,
    fetch_url_content,
)


def get_user_urls():
    """Get URLs from user input."""
    print("🌐 Browser Use Module - Interactive Example")
    print("=" * 50)
    print("请输入要抓取的URL（可输入多个，每行一个，输入空行结束）:")
    print("示例: https://example.com")
    print("     https://news.ycombinator.com")
    print("     https://github.com")
    print()

    urls = []
    while True:
        url = input(f"URL {len(urls) + 1} (回车结束): ").strip()
        if not url:
            break
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        urls.append(url)

    if not urls:
        print("未输入URL，使用默认示例URL...")
        urls = [
            "https://httpbin.org/html",
            "https://example.com",
        ]

    return urls


def get_user_preferences():
    """Get user preferences for fetching."""
    print("\n⚙️ 配置选项:")

    # Headless mode
    headless_input = input("是否使用无头模式? (y/n, 默认: y): ").strip().lower()
    headless = headless_input != "n"

    # Timeout
    timeout_input = input("超时时间 (秒, 默认: 30): ").strip()
    try:
        timeout = float(timeout_input) if timeout_input else 30.0
    except ValueError:
        timeout = 30.0

    # Example type
    print("\n📋 选择示例类型:")
    print("1. 基础抓取 (快速获取页面内容)")
    print("2. 批量处理 (使用同一浏览器实例)")
    print("3. 全部运行")
    
    example_choice = input("请选择 (1-3, 默认: 3): ").strip()

    return {
        "headless": headless,
        "timeout": timeout,
        "example_type": example_choice or "3",
    }


async def basic_fetch_example(urls, headless=True, timeout=30.0):
    """Basic example of fetching content from URLs."""
    print("\n=== 基础抓取示例 ===")

    for i, url in enumerate(urls, 1):
        print(f"\n{i}. 抓取: {url}")
        result = await fetch_url_content(url, headless=headless, timeout=timeout)

        if result["success"]:
            print(f"   ✓ 成功抓取")
            print(f"   📄 标题: {result['title']}")
            print(f"   📝 内容长度: {len(result['content'])} 字符")
            print(f"   📊 字数: {result['metadata']['word_count']}")
            print(f"   🔗 链接数: {result['metadata']['link_count']}")
            print(f"   🖼️ 图片数: {result['metadata']['image_count']}")
            print(f"   📡 状态码: {result['status_code']}")

            # Show content preview
            content_preview = (
                result["content"][:1000] + "..."
                if len(result["content"]) > 1000
                else result["content"]
            )
            print(f"   📖 内容预览: {content_preview}")
        else:
            print(f"   ✗ 抓取失败: {result['error']}")


async def batch_processing_example(urls, headless=True, timeout=30.0):
    """Example using BrowserFetch as a context manager for multiple requests."""
    print("\n=== 批量处理示例 ===")
    print("使用同一浏览器实例处理多个URL，提高效率...")

    async with BrowserFetch(headless=headless, timeout=timeout) as fetcher:
        print(f"🚀 开始批量处理 {len(urls)} 个URL...")

        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n{i}/{len(urls)} 处理: {url}")
            result = await fetcher.fetch_content(url)
            results.append((url, result))

            if result["success"]:
                print(f"   ✓ 成功 - {result['metadata']['word_count']} 字")
            else:
                print(f"   ✗ 失败 - {result['error']}")

        # Summary
        print(f"\n📊 批量处理总结:")
        successful = sum(1 for _, result in results if result["success"])
        print(f"   成功: {successful}/{len(urls)}")
        print(f"   失败: {len(urls) - successful}/{len(urls)}")

        if successful > 0:
            total_words = sum(
                result["metadata"]["word_count"]
                for _, result in results
                if result["success"]
            )
            print(f"   总字数: {total_words}")


async def debug_mode_example(urls, timeout=30.0):
    """Example of running in debug mode (visible browser)."""
    print("\n=== 调试模式示例 ===")
    print("⚠️ 注意: 这将打开可见的浏览器窗口")

    confirm = input("是否继续? (y/n): ").strip().lower()
    if confirm == "y":
        url = urls[0] if urls else "https://example.com"
        print(f"🔍 调试模式抓取: {url}")

        async with BrowserFetch(headless=False, timeout=timeout) as fetcher:
            result = await fetcher.fetch_content(url)
            if result["success"]:
                print(f"✓ 调试抓取成功: {result['title']}")
            else:
                print(f"✗ 调试抓取失败: {result['error']}")
    else:
        print("跳过调试模式示例")


async def main():
    """Run interactive examples."""
    try:
        # Get user input
        urls = get_user_urls()
        preferences = get_user_preferences()

        print(f"\n🎯 将处理 {len(urls)} 个URL:")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")

        print(f"\n⚙️ 配置:")
        print(f"   无头模式: {'是' if preferences['headless'] else '否'}")
        print(f"   超时时间: {preferences['timeout']} 秒")

        # Run selected examples
        example_type = preferences["example_type"]

        if example_type in ["1", "3"]:
            await basic_fetch_example(
                urls, preferences["headless"], preferences["timeout"]
            )

        if example_type in ["2", "3"]:
            await batch_processing_example(
                urls, preferences["headless"], preferences["timeout"]
            )

        # Debug mode (only if not headless)
        if not preferences["headless"] and example_type == "3":
            await debug_mode_example(urls, preferences["timeout"])

        print("\n" + "=" * 50)
        print("🎉 所有示例完成!")
        print("\n💡 提示:")
        print("   - 使用无头模式可以提高性能")
        print("   - 批量处理可以复用浏览器实例，提高效率")
        print("   - 调试模式可以观察浏览器实际操作过程")

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        print("\n🔧 请确保已安装必要的依赖:")
        print("   pip install playwright loguru")
        print("   playwright install firefox")


if __name__ == "__main__":
    asyncio.run(main())
