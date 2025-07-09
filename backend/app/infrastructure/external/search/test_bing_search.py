import asyncio
import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)

from app.infrastructure.external.search.bing_search import BingSearchEngine

async def test_bing_search():
    search_engine = BingSearchEngine()
    
    # Test 1: Basic search
    print("\n=== Test 1: Basic Search ===")
    result = await search_engine.search("Python 编程教程")
    if result.success:
        print(f"Found {len(result.data['results'])} results")
        print("\nFirst 3 results:")
        for i, item in enumerate(result.data['results'][:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Link: {item['link']}")
            print(f"   Snippet: {item['snippet'][:100]}...")
    else:
        print(f"Search failed: {result.message}")
    
    # Test 2: Search with date range
    print("\n=== Test 2: Search with Date Range ===")
    result = await search_engine.search("OpenAI GPT", date_range="past_month")
    if result.success:
        print(f"Found {len(result.data['results'])} results from past month")
        print("\nFirst 3 results:")
        for i, item in enumerate(result.data['results'][:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Link: {item['link']}")
            print(f"   Snippet: {item['snippet'][:100]}...")
    else:
        print(f"Search failed: {result.message}")

if __name__ == "__main__":
    asyncio.run(test_bing_search()) 