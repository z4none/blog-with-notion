#!/usr/bin/env python3
"""
Quick proxy test - simplified version
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_proxy_simple():
    """Simple test to see if proxy works"""
    try:
        from notion_sync.config import get_config
        config = get_config()
        
        if config and config.notion and config.notion.proxy_url:
            print(f"[INFO] Proxy configured: {config.notion.proxy_url}")
            
            # Set environment variables for proxy
            os.environ['HTTP_PROXY'] = config.notion.proxy_url
            os.environ['HTTPS_PROXY'] = config.notion.proxy_url
            
            # Try a simple HTTP request to test proxy
            import requests
            response = requests.get('https://www.notion.so/api/v3/getUserPreferences', timeout=10)
            print(f"[SUCCESS] Proxy connection working! Status: {response.status_code}")
            return True
        else:
            print("[INFO] No proxy configured")
            return False
            
    except Exception as e:
        print(f"[ERROR] Proxy test failed: {e}")
        return False

if __name__ == "__main__":
    test_proxy_simple()