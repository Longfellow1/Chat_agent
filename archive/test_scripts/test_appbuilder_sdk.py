"""Test using official AppBuilder SDK."""
import os
import appbuilder

os.environ["APPBUILDER_TOKEN"] = "REDACTED"
APP_ID = "app-pQDPdqf4"

print("=" * 60)
print("使用官方 AppBuilder SDK 测试")
print("=" * 60)

try:
    # 初始化
    client = appbuilder.AppBuilderClient(APP_ID)
    print("✓ 初始化成功")
    
    # 创建会话
    conversation_id = client.create_conversation()
    print(f"✓ 会话ID: {conversation_id}")
    
    # 运行对话
    result = client.run(conversation_id, "什么是电动汽车", stream=False)
    print(f"✓ 对话成功")
    print(f"\n回答:\n{result.content.answer}")
    
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()
