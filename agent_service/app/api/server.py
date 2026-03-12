from __future__ import annotations

import os
import time
from contextvars import ContextVar
from pathlib import Path

# Load .env.agent file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / ".env.agent"  # 4个parent到项目根目录
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, try manual load
    env_path = Path(__file__).parent.parent.parent.parent / ".env.agent"  # 4个parent到项目根目录
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

from app.factory import build_flow
from app.schemas.contracts import ChatRequest
from app.schemas.errors import BAD_JSON, BACKEND_UNAVAILABLE, INTERNAL_ERROR, INVALID_REQUEST
from app.schemas.http_models import ChatRequestBody
from infra.observability.tracing import gen_trace_id, write_trace
from domain.trip.tool_streaming import plan_trip_streaming
from domain.intents.trip_router import route_trip_intent
from infra.tool_clients.amap_mcp_client import AmapMCPClient

_trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")
_flow = None  # 延迟初始化


def get_flow():
    """获取ChatFlow实例（延迟初始化）"""
    global _flow
    if _flow is None:
        _flow = build_flow()
    return _flow


def get_trace_id() -> str:
    return _trace_id_ctx.get() or gen_trace_id()


app = FastAPI(title="Agent Service", version="0.1.0")


@app.middleware("http")
async def with_trace(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id") or gen_trace_id()
    token = _trace_id_ctx.set(trace_id)
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        cost = int((time.perf_counter() - t0) * 1000)
        write_trace(
            {
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
                "latency_ms": cost,
                "source": "middleware",
            }
        )
        _trace_id_ctx.reset(token)
    response.headers["x-trace-id"] = trace_id
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequestBody):
    trace_id = get_trace_id()
    query = req.query.strip()
    if not query:
        err = INVALID_REQUEST
        raise HTTPException(status_code=err.http_status, detail={"code": err.code, "message": err.message})

    start = time.perf_counter()
    try:
        out = get_flow().run(ChatRequest(query=query, session_id=req.session_id, user_id=req.user_id))
    except RuntimeError as e:
        err = BACKEND_UNAVAILABLE
        write_trace(
            {
                "trace_id": trace_id,
                "source": "chat",
                "stage": "llm",
                "error": str(e),
            }
        )
        return JSONResponse(
            status_code=err.http_status,
            content={"code": err.code, "message": f"{err.message}: {e}", "trace_id": trace_id, "data": {}},
        )
    except Exception as e:  # noqa: BLE001
        err = INTERNAL_ERROR
        write_trace(
            {
                "trace_id": trace_id,
                "source": "chat",
                "stage": "unknown",
                "error": str(e),
            }
        )
        return JSONResponse(
            status_code=err.http_status,
            content={"code": err.code, "message": err.message, "trace_id": trace_id, "data": {}},
        )

    cost = int((time.perf_counter() - start) * 1000)
    payload = out.to_dict()
    payload.setdefault("latency_ms", {})
    payload["latency_ms"]["total"] = cost
    write_trace(
        {
            "trace_id": trace_id,
            "source": "chat",
            "query": query,
            "effective_query": payload.get("effective_query"),
            "rewritten": payload.get("rewritten"),
            "rewrite_source": payload.get("rewrite_source"),
            "route_source": payload.get("route_source"),
            "decision_mode": payload.get("decision_mode"),
            "tool_name": payload.get("tool_name"),
            "tool_status": payload.get("tool_status"),
            "tool_provider": payload.get("tool_provider"),
            "tool_error": payload.get("tool_error"),
            "fallback_chain": payload.get("fallback_chain"),
            "post_llm_applied": payload.get("post_llm_applied"),
            "post_llm_timeout": payload.get("post_llm_timeout"),
            "latency_ms": payload.get("latency_ms"),
        }
    )
    return {"code": "0", "message": "ok", "trace_id": trace_id, "data": payload}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequestBody):
    """Streaming chat endpoint for plan_trip queries."""
    import json
    
    trace_id = get_trace_id()
    query = req.query.strip()
    
    if not query:
        err = INVALID_REQUEST
        raise HTTPException(status_code=err.http_status, detail={"code": err.code, "message": err.message})
    
    async def generate():
        """Generate SSE stream."""
        try:
            # Check if this is a plan_trip query
            is_trip, params, _ = route_trip_intent(query)
            
            if is_trip and params.get("destination"):
                # Stream plan_trip output
                amap_client = AmapMCPClient()
                
                async for chunk in plan_trip_streaming(
                    destination=params["destination"],
                    days=params.get("days", 2),
                    travel_mode=params.get("travel_mode", "transit"),
                    preferences=params.get("preferences"),
                    amap_client=amap_client
                ):
                    # SSE format: data: {json}\n\n
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # Log trace
                write_trace({
                    "trace_id": trace_id,
                    "source": "chat_stream",
                    "query": query,
                    "tool_name": "plan_trip",
                    "streaming": True
                })
            else:
                # Non-plan_trip query: fall back to regular flow
                out = get_flow().run(ChatRequest(query=query, session_id=req.session_id, user_id=req.user_id))
                
                # Send as single chunk
                yield f"data: {json.dumps({'type': 'complete', 'text': out.final_text, 'data': out.to_dict()}, ensure_ascii=False)}\n\n"
                
                write_trace({
                    "trace_id": trace_id,
                    "source": "chat_stream",
                    "query": query,
                    "tool_name": out.to_dict().get("tool_name"),
                    "streaming": False
                })
        
        except Exception as e:
            logger.error(f"Error in chat_stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'text': f'处理失败: {str(e)}', 'data': {'error': str(e)}}, ensure_ascii=False)}\n\n"
            
            write_trace({
                "trace_id": trace_id,
                "source": "chat_stream",
                "query": query,
                "error": str(e)
            })
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Trace-ID": trace_id
        }
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException):
    trace_id = get_trace_id()
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": INVALID_REQUEST.code, "message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": detail.get("code", INVALID_REQUEST.code),
            "message": detail.get("message", INVALID_REQUEST.message),
            "trace_id": trace_id,
            "data": {},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    trace_id = get_trace_id()
    err = INVALID_REQUEST
    for item in exc.errors():
        if item.get("type") == "json_invalid":
            err = BAD_JSON
            break
    return JSONResponse(
        status_code=err.http_status,
        content={
            "code": err.code,
            "message": err.message,
            "trace_id": trace_id,
            "data": {},
        },
    )


def run_server() -> None:
    import socket
    import uvicorn

    host = os.getenv("AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", "8000"))
    
    # Auto-find available port if default is occupied
    def find_free_port(start_port: int, max_attempts: int = 10) -> int:
        for offset in range(max_attempts):
            try_port = start_port + offset
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((host, try_port))
                    return try_port
                except OSError:
                    continue
        raise RuntimeError(f"No free port found in range {start_port}-{start_port + max_attempts - 1}")
    
    port = find_free_port(port)
    print(f"Starting server on {host}:{port}")
    uvicorn.run("app.api.server:app", host=host, port=port, reload=False)
