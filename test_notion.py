#!/usr/bin/env python3
"""
Test script for Notion sync functionality
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notion_sync.config import SyncConfig, get_config
from notion_sync.notion_client import NotionClient

async def test_notion_connection():
    """Test the Notion client connection and methods"""
    try:
        print("Testing Notion connection...")
        
        # Load config
        config = get_config()
        if not config or not config.notion or not config.notion.token:
            print("ERROR: No Notion token found in config")
            return False
        
        # Initialize client
        client = NotionClient(config.notion)
        
        # Test get_posts
        print("\n1. Testing get_posts()...")
        posts = await client.get_posts()
        print(f"[OK] get_posts() returned {len(posts)} posts")
        
        if posts:
            # Test get_page_content for first post
            print("\n2. Testing get_page_content()...")
            content = await client.get_page_content(posts[0].id)
            print(f"[OK] get_page_content() returned {len(content)} characters")
            
            # Test database pages
            print("\n3. Testing database methods...")
            if posts[0].database_id:
                db_posts = await client.get_database_pages(posts[0].database_id)
                print(f"[OK] get_database_pages() returned {len(db_posts)} database posts")
            else:
                print("- No database_id found for first post")
        
        print("\n[SUCCESS] All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_notion_connection())
    sys.exit(0 if success else 1)