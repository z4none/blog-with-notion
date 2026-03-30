#!/usr/bin/env python3
"""
Debug notion_client API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_client():
    """Debug notion_client behavior"""
    from notion_sync.config import get_config
    from notion_client import Client
    
    config = get_config()
    if config and config.notion and config.notion.proxy_url:
        os.environ['HTTP_PROXY'] = config.notion.proxy_url
        os.environ['HTTPS_PROXY'] = config.notion.proxy_url
    
    client = Client(auth=config.notion.token)
    
    # Check what client.search actually is
    print(f"client.search type: {type(client.search)}")
    print(f"client.search callable: {callable(client.search)}")
    
    # Try to call it directly (without await)
    try:
        result = client.search(limit=1)
        print(f"Direct call successful: {type(result)}")
        print(f"Result has .get: {hasattr(result, 'get')}")
    except Exception as e:
        print(f"Direct call failed: {e}")
        
    # Check blocks.children.list
    print(f"\nTesting blocks.children.list...")
    blocks_endpoint = client.blocks.children
    print(f"blocks.children.list type: {type(blocks_endpoint.list)}")
    
    # Try to call it directly
    try:
        # Use a dummy page ID for testing
        result = blocks_endpoint.list(block_id="test")
        print(f"blocks.list call type: {type(result)}")
    except Exception as e:
        print(f"blocks.list call failed: {e}")
        
    # Try with asyncio
    import asyncio
    try:
        result = asyncio.run(blocks_endpoint.list(block_id="test"))
        print(f"blocks.list async call type: {type(result)}")
    except Exception as e2:
        print(f"blocks.list async call failed: {e2}")

if __name__ == "__main__":
    debug_client()