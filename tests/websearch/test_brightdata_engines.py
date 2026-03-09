"""
Test script to compare Bing and Yandex search results with different data formats.

This script tests:
1. Bing with data_format='parsed'
2. Bing with data_format='markdown'
3. Yandex with data_format='parsed'
4. Yandex with data_format='markdown'

Run with: python -m pytest tests/websearch/test_brightdata_engines.py -v -s
Or directly: python tests/websearch/test_brightdata_engines.py
"""

import json
import os
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def build_search_url(engine: str, query: str, page: int = 0) -> str:
    """Build search URL for different engines."""
    q = quote_plus(query)  # URL encode the query
    start = page * 10

    if engine == "yandex":
        return f"https://yandex.com/search/?text={q}&p={page}"
    elif engine == "bing":
        return f"https://www.bing.com/search?q={q}&first={start + 1}"
    else:  # google
        return f"https://www.google.com/search?q={q}&start={start}"


def run_engine_format(engine: str, data_format: str, query: str = "python programming"):
    """Run a specific engine with a specific data format (manual test helper)."""
    api_token = os.getenv("BRIGHTDATA_API_KEY")
    if not api_token:
        print("❌ BRIGHTDATA_API_KEY not set")
        return None

    zone = os.getenv("BRIGHTDATA_ZONE", "mcp_unlocker")

    # Build search URL
    search_url = build_search_url(engine, query, page=0)

    # Add brd_json flag for Google parsed format
    if engine == "google" and data_format == "parsed":
        search_url += "&brd_json=1"

    # Prepare request
    payload = {
        "url": search_url,
        "zone": zone,
        "format": "raw",
    }

    # Only add data_format if not using default
    if data_format:
        payload["data_format"] = data_format

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print(f"\n{'=' * 80}")
    print(f"🔍 Testing: {engine.upper()} with data_format='{data_format}'")
    print(f"{'=' * 80}")
    print(f"Search URL: {search_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.brightdata.com/request",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            result_text = response.text

            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📏 Response Length: {len(result_text)} characters")
            print(f"\n{'─' * 80}")
            print("📄 Response Preview (first 2000 chars):")
            print(f"{'─' * 80}")
            print(result_text[:2000])

            if len(result_text) > 2000:
                print(f"\n... (truncated, total {len(result_text)} chars)")

            # Try to parse as JSON
            try:
                data = json.loads(result_text)
                print(f"\n{'─' * 80}")
                print("🔑 JSON Structure Keys:")
                print(f"{'─' * 80}")
                print(json.dumps(list(data.keys()), indent=2))

                # Show organic results if available
                if "organic" in data:
                    print(
                        f"\n📋 Number of organic results: {len(data.get('organic', []))}"
                    )
                    if data["organic"]:
                        print(f"\n{'─' * 80}")
                        print("🎯 First Organic Result:")
                        print(f"{'─' * 80}")
                        print(
                            json.dumps(data["organic"][0], indent=2, ensure_ascii=False)
                        )

                # Save full response to file
                filename = f"brightdata_{engine}_{data_format}_response.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Full response saved to: {filename}")

            except json.JSONDecodeError:
                print("\n⚠️  Response is not JSON (likely Markdown)")
                # Save as text file
                filename = f"brightdata_{engine}_{data_format}_response.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(result_text)
                print(f"💾 Full response saved to: {filename}")

            return result_text

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def main():
    """Run all tests."""
    query = "artificial intelligence"

    print("\n" + "=" * 80)
    print("🧪 Bright Data Search Engine Format Comparison Test")
    print("=" * 80)

    # Test configurations
    tests = [
        ("bing", "parsed"),
        ("bing", "markdown"),
        ("yandex", "parsed"),
        ("yandex", "markdown"),
        ("google", "parsed"),  # For comparison
    ]

    results = {}
    for engine, data_format in tests:
        result = run_engine_format(engine, data_format, query)
        results[f"{engine}_{data_format}"] = result

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    for key, result in results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"{key:25s} {status}")

    print("\n" + "=" * 80)
    print("💡 Key Findings:")
    print("=" * 80)
    print("1. Check the generated files to see the actual response formats")
    print("2. Compare JSON structure vs Markdown output")
    print("3. Determine which format is easier to parse for each engine")
    print("=" * 80)


if __name__ == "__main__":
    main()
