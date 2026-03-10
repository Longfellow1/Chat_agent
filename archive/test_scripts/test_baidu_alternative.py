"""Try alternative Baidu API formats."""

import json
import requests

ACCESS_KEY = "REDACTED"


def test_format_1():
    """Test format 1: conversation API."""
    print("=" * 60)
    print("测试格式 1: conversation API")
    print("=" * 60)
    
    url = "https://qianfan.baidubce.com/v2/app/conversation"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_KEY}",
    }
    
    payload = {
        "query": "什么是电动汽车",
        "stream": False,
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}\n")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def test_format_2():
    """Test format 2: chat completions."""
    print("=" * 60)
    print("测试格式 2: chat completions")
    print("=" * 60)
    
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_KEY}",
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": "什么是电动汽车"}
        ],
        "stream": False,
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}\n")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def test_format_3():
    """Test format 3: with conversation_id."""
    print("=" * 60)
    print("测试格式 3: with conversation_id")
    print("=" * 60)
    
    url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_KEY}",
    }
    
    payload = {
        "conversation_id": "",
        "query": "什么是电动汽车",
        "stream": False,
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}\n")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    test_format_1()
    test_format_2()
    test_format_3()
