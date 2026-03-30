#!/usr/bin/env python3
"""
Test Notion client with proxy
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notion_sync.config import SyncConfig, get_config
from notion_sync.notion_client import NotionClient

async def test_proxy():
    """Test Notion client with proxy"""
    try:
        print("Testing Notion connection with proxy...")
        
        # Load config
        config = get_config()
        if not config or not config.notion or not config.notion.token:
            print("ERROR: No Notion token found in config")
            return False
        
        # Initialize client (will use proxy if configured)
        client = NotionClient(config.notion)
        
        # Test get_posts
        print("\n1. Testing get_posts() with proxy...")
        posts = client.get_posts()  # Now it's synchronous
        print(f"[OK] get_posts() returned {len(posts)} posts")
        
        if len(posts) > 0:
            print("\n[SUCCESS] Proxy connection successful!")
            print(f"Found {len(posts)} posts/pages in Notion")
        else:
            print("\n[INFO] Connected but no posts found (might be normal for new setup)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("[INFO] Testing Notion connection with proxy support...")
    success = test_proxy()  # Now it's synchronous
    sys.exit(0 if success else 1)