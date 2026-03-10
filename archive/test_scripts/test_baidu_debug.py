"""Debug Baidu API calls."""

import json
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent_service"))

# Set real key
ACCESS_KEY = "REDACTED"


def test_baidu_baike_raw():
    """Test Baidu Baike API directly."""
    print("=" * 60)
    print("测试百度百科 API (原始调用)")
    print("=" * 60)
    
    url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_KEY}",
    }
    
    payload = {
        "app_id": "baidu_baike",
        "query": "什么是电动汽车",
        "stream": False,
    }
    
    print(f"\nURL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


def test_baidu_search_mcp_raw():
    """Test Baidu Search MCP API directly."""
    print("\n" + "=" * 60)
    print("测试百度搜索 MCP API (原始调用)")
    print("=" * 60)
    
    url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_KEY}",
    }
    
    payload = {
        "app_id": "mcp_baidu_web_search",
        "query": "特斯拉 Model 3 价格",
        "stream": False,
        "tools": [
            {
                "type": "baidu_search",
                "baidu_search": {
                    "top_n": 5
                }
            }
        ]
    }
    
    print(f"\nURL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_baidu_baike_raw()
    test_baidu_search_mcp_raw()
