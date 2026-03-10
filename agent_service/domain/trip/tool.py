"""Plan trip tool interface."""

from __future__ import annotations

import logging
from typing import Dict, Any

from domain.tools.types import ToolResult
from domain.trip.engine import TripPlannerEngine
from infra.tool_clients.amap_mcp_client import AmapMCPClient

logger = logging.getLogger(__name__)


async def plan_trip(
    destination: str,
    days: int = 2,
    travel_mode: str = "transit",
    preferences: list = None,  # M5.2: 用户偏好列表
    amap_client: AmapMCPClient | None = None
) -> ToolResult:
    """
    Plan a trip itinerary.
    
    Args:
        destination: Destination city
        days: Number of days (default: 2)
        travel_mode: Travel mode ("transit" or "driving", default: "transit")
        preferences: User preferences list (M5.2: ["food", "entertainment", etc.])
        amap_client: Amap MCP client instance
    
    Returns:
        ToolResult with trip itinerary
    """
    if not destination:
        return ToolResult(
            ok=False,
            text="请提供目的地城市",
            error="missing_destination"
        )
    
    if not amap_client:
        return ToolResult(
            ok=False,
            text="高德MCP服务不可用",
            error="amap_mcp_unavailable"
        )
    
    try:
        # Create trip planner engine
        engine = TripPlannerEngine(amap_client)
        
        # Plan trip (M5.2: 传递preferences参数)
        itinerary = await engine.plan(destination, days, travel_mode, user_prefs=preferences)
        
        # Check if empty
        if not itinerary.itinerary:
            return ToolResult(
                ok=False,
                text=f"未找到{destination}的景点信息，请尝试其他目的地",
                error="no_attractions_found"
            )
        
        # Format as text
        text = _format_itinerary_text(itinerary, preferences)
        
        return ToolResult(
            ok=True,
            text=text,
            raw={
                "provider": "amap_mcp",
                "destination": destination,
                "days": days,
                "travel_mode": travel_mode,
                "preferences": preferences,  # M5.2: 包含偏好信息
                "itinerary": itinerary.to_dict()
            }
        )
    
    except Exception as e:
        logger.error(f"Error planning trip: {e}")
        return ToolResult(
            ok=False,
            text=f"行程规划失败: {str(e)}",
            error=str(e)
        )


def _format_itinerary_text(itinerary, preferences=None) -> str:
    """Format itinerary as readable text."""
    lines = [f"{itinerary.destination}{itinerary.days}日游行程规划：\n"]
    
    # M5.4: 如果有偏好，说明选择了哪些偏好
    if preferences:
        pref_names = {
            "food": "美食",
            "entertainment": "娱乐",
            "culture": "文化",
            "nature": "自然",
            "shopping": "购物",
            "relax": "休闲"
        }
        pref_text = "、".join([pref_names.get(p, p) for p in preferences])
        lines.append(f"（已为您优选{pref_text}相关景点）\n")
    
    for day_plan in itinerary.itinerary:
        lines.append(f"\n第{day_plan.day}天 - {day_plan.theme}\n")
        
        for session in day_plan.sessions:
            lines.append(f"\n{session.period}")
            
            for stop in session.stops:
                lines.append(f"• [第{stop.order}站] {stop.name}（{stop.address}）")
                
                if stop.transit_to_next:
                    lines.append(f"  交通：{stop.transit_to_next.description}")
        
        # M5.1: Add dinner recommendations (产品表达调整)
        if day_plan.dinner_recommendations:
            lines.append(f"\n今日精选餐厅")  # 改为"今日精选"而非"附近推荐"
            for restaurant in day_plan.dinner_recommendations:
                lines.append(f"• {restaurant['name']}")
    
    return "\n".join(lines)
