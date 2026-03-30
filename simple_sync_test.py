#!/usr/bin/env python3
"""
Simple sync test without async issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simple_sync_test():
    """Test sync with minimal async issues"""
    try:
        from notion_sync.config import get_config
        from notion_sync.notion_client import NotionClient
        
        config = get_config()
        if not config or not config.notion or not config.notion.token:
            print("ERROR: No Notion token found")
            return False
            
        # Set proxy
        if config.notion.proxy_url:
            os.environ['HTTP_PROXY'] = config.notion.proxy_url
            os.environ['HTTPS_PROXY'] = config.notion.proxy_url
            print(f"[INFO] Using proxy: {config.notion.proxy_url}")
        
        client = NotionClient(config.notion)
        
        # Test get_posts
        print("[INFO] Testing get_posts()...")
        posts = client.get_posts()
        print(f"[SUCCESS] Found {len(posts)} posts")
        
        # Find project posts
        project_posts = [post for post in posts if post.is_project()]
        print(f"[INFO] Found {len(project_posts)} project posts")
        
        if project_posts:
            print("\nProjects found:")
            for post in project_posts[:5]:  # Show first 5
                print(f"  - {post.title} ({post.project_status or 'No status'})")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("[INFO] Simple sync test...")
    success = simple_sync_test()
    print(f"\n{'SUCCESS' if success else 'FAILED'}: Sync test {'passed' if success else 'failed'}")
    sys.exit(0 if success else 1)