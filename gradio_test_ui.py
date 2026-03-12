#!/usr/bin/env python3
"""
Gradio测试界面 - 快速手动测试Agent服务
直接使用CLI模式避免循环导入
"""
import os
import sys
import json
import subprocess
import gradio as gr
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env.agent"
if env_path.exists():
    load_dotenv(env_path)


def chat_interface(query: str, session_id: str = "") -> tuple[str, str]:
    """处理聊天请求 - 使用CLI模式"""
    if not query.strip():
        return "请输入问题", ""
    
    try:
        # 使用CLI模式调用 - 直接调用main.py
        cmd = [
            str(Path(__file__).parent / ".venv" / "bin" / "python"),
            str(Path(__file__).parent / "agent_service" / "main.py"),
            "chat",
            query.strip()
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent / "agent_service")}
        )
        
        if result.returncode != 0:
            return f"❌ 错误: {result.stderr}", ""
        
        # 解析JSON响应
        response = json.loads(result.stdout)
        
        # 主要回复
        answer = response.get("final_text", "无回复")
        
        # 调试信息
        debug_info = {
            "决策模式": response.get("decision_mode"),
            "工具名称": response.get("tool_name"),
            "工具参数": response.get("tool_args"),
            "工具状态": response.get("tool_status"),
            "工具提供商": response.get("tool_provider"),
            "路由来源": response.get("route_source"),
            "提取来源": response.get("extract_source"),
            "延迟(ms)": response.get("latency_ms"),
            "意图概率": response.get("intent_probs"),
        }
        
        # 移除None值
        debug_info = {k: v for k, v in debug_info.items() if v is not None}
        
        debug_text = json.dumps(debug_info, ensure_ascii=False, indent=2)
        
        return answer, debug_text
        
    except subprocess.TimeoutExpired:
        return "❌ 请求超时", ""
    except json.JSONDecodeError as e:
        return f"❌ 解析错误: {str(e)}", result.stdout if 'result' in locals() else ""
    except Exception as e:
        return f"❌ 错误: {str(e)}", f"异常详情:\n{type(e).__name__}: {str(e)}"


# 创建Gradio界面
with gr.Blocks(title="Agent测试界面") as demo:
    gr.Markdown("# 🤖 Agent服务测试界面")
    gr.Markdown("快速测试工具调用和聊天链路")
    
    with gr.Row():
        with gr.Column(scale=2):
            query_input = gr.Textbox(
                label="输入问题",
                placeholder="例如: 北京今天天气怎么样？",
                lines=2
            )
            session_input = gr.Textbox(
                label="Session ID (可选)",
                placeholder="留空则不使用会话",
                lines=1
            )
            submit_btn = gr.Button("🚀 发送", variant="primary", size="lg")
            
        with gr.Column(scale=1):
            gr.Markdown("### 快速测试用例")
            gr.Markdown("**天气查询 (get_weather)**")
            gr.Markdown("- 预期: tool_call/get_weather")
            examples_weather = gr.Examples(
                examples=[
                    ["北京今天天气怎么样"],
                    ["请查一下长沙下周二气温大概多少"],
                ],
                inputs=query_input
            )
            
            gr.Markdown("**股票查询 (get_stock)**")
            gr.Markdown("- 预期: tool_call/get_stock")
            examples_stock = gr.Examples(
                examples=[
                    ["帮我看招商银行实时行情"],
                    ["请查看比亚迪今天股价"],
                    ["茅台现在多少钱"],
                ],
                inputs=query_input
            )
            
            gr.Markdown("**新闻查询 (get_news)**")
            gr.Markdown("- 预期: tool_call/get_news")
            examples_news = gr.Examples(
                examples=[
                    ["我想看今天国际局势热点"],
                    ["我想看今天医药热点"],
                ],
                inputs=query_input
            )
            
            gr.Markdown("**地点查询 (find_nearby)**")
            gr.Markdown("- 预期: tool_call/find_nearby")
            examples_nearby = gr.Examples(
                examples=[
                    ["帮我找合肥天河周边的加油站"],
                    ["济南解放碑附近有什么商场"],
                    ["帮我找成都东部新城周边的景点"],
                    ["帮我找福州和平路周边的停车场"],
                ],
                inputs=query_input
            )
            
            gr.Markdown("**旅游规划 (plan_trip)**")
            gr.Markdown("- 预期: tool_call/plan_trip")
            examples_trip = gr.Examples(
                examples=[
                    ["帮我规划青岛4天旅游行程"],
                ],
                inputs=query_input
            )
            
            gr.Markdown("**搜索查询 (web_search)**")
            gr.Markdown("- 预期: tool_call/web_search")
            examples_search = gr.Examples(
                examples=[
                    ["请检索品牌口碑"],
                ],
                inputs=query_input
            )
            
            gr.Markdown("**闲聊/知识 (reply)**")
            gr.Markdown("- 预期: reply")
            examples_chat = gr.Examples(
                examples=[
                    ["我好难过，能陪我聊聊吗"],
                    ["请简单解释十二生肖"],
                    ["用一句话说说你的功能"],
                    ["我有点无聊陪我聊会儿"],
                ],
                inputs=query_input
            )
    
    with gr.Row():
        with gr.Column():
            answer_output = gr.Textbox(
                label="📝 回复",
                lines=8
            )
            copy_answer_btn = gr.Button("📋 复制回复", size="sm")
        
        with gr.Column():
            debug_output = gr.Textbox(
                label="🔍 调试信息",
                lines=8
            )
            copy_debug_btn = gr.Button("📋 复制调试信息", size="sm")
    
    # 绑定事件
    submit_btn.click(
        fn=chat_interface,
        inputs=[query_input, session_input],
        outputs=[answer_output, debug_output]
    )
    
    query_input.submit(
        fn=chat_interface,
        inputs=[query_input, session_input],
        outputs=[answer_output, debug_output]
    )
    
    # 复制按钮事件
    copy_answer_btn.click(
        fn=lambda x: x,
        inputs=[answer_output],
        outputs=[],
        js="(x) => {navigator.clipboard.writeText(x); return x;}"
    )
    
    copy_debug_btn.click(
        fn=lambda x: x,
        inputs=[debug_output],
        outputs=[],
        js="(x) => {navigator.clipboard.writeText(x); return x;}"
    )
    
    gr.Markdown("---")
    gr.Markdown("💡 提示: 确保后端服务已启动，环境变量已配置")


if __name__ == "__main__":
    # 检查环境
    backend = os.getenv("AGENT_BACKEND", "lmstudio")
    print(f"✅ 后端: {backend}")
    print(f"✅ 环境文件: {env_path}")
    
    # 启动界面 - 使用独立端口避免冲突
    demo.launch(
        server_name="0.0.0.0",
        server_port=7870,  # 使用7870避免与主线8000端口冲突
        share=False,
        show_error=True,
        theme=gr.themes.Soft()
    )
