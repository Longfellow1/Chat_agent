import os
import appbuilder

os.environ["APPBUILDER_TOKEN"] = "REDACTED"

# 尝试不同的 APP ID 格式
app_ids = [
    "app-pQDPdqf4",
    "pQDPdqf4",
    "APP-pQDPdqf4",
]

for app_id in app_ids:
    print(f"\n{'='*60}")
    print(f"测试 APP ID: {app_id}")
    print('='*60)
    
    try:
        client = appbuilder.AppBuilderClient(app_id)
        conversation_id = client.create_conversation()
        print(f"✓ 成功! 会话ID: {conversation_id}")
        break
    except Exception as e:
        error_msg = str(e)
        if "InvalidRequestArgumentError" in error_msg:
            print(f"✗ 无效的请求参数")
        elif "invalid_model" in error_msg:
            print(f"✗ 无效的模型")
        else:
            print(f"✗ {error_msg[:100]}")
