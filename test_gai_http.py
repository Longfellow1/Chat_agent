#!/usr/bin/env python3
import requests
import json

response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "GAI是谁"},
    timeout=15
)

data = response.json()
print(f"Tool: {data.get('tool_name')}")
print(f"Mode: {data.get('decision_mode')}")
print(f"Route: {data.get('route_source')}")
print(f"Final Text: {data.get('final_text')[:100]}")
