"""Plan trip streaming tool interface."""

from __future__ import annotations

import logging
from typing import Dict, Any, AsyncGenerator

from domain.trip.engine import TripPlannerEngine
from infra.tool_clients.amap_mcp_client import AmapMCPClient

logger = logging.getLogger(__name__)


async def plan_trip_streaming(
    destination: str,
    days: int = 2,
    travel_mode: str = "transit",
    preferences: list = None,
    amap_client: AmapMCPClient | None = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Plan a trip itinerary with streaming output.
    
    Yields chunks in the following format:
    {
        "type": "day_header" | "session" | "stop" | "transit" | "restaurant_header" | "restaurant" | "complete" | "error",
        "text": str,  # Human-readable text
        "data": dict  # Structured data (optional)
    }
    
    Args:
        destination: Destination city
        days: Number of days (default: 2)
        travel_mode: Travel mode ("transit" or "driving", default: "transit")
        preferences: User preferences list (["food", "entertainment", etc.])
        amap_client: Amap MCP client instance
    
    Yields:
        Dict chunks with streaming output
    """
    if not destination:
        yield {
            "type": "error",
            "text": "请提供目的地城市",
            "data": {"error": "missing_destination"}
        }
        return
    
    if not amap_client:
        yield {
            "type": "error",
            "text": "高德MCP服务不可用",
            "data": {"error": "amap_mcp_unavailable"}
        }
        return
    
    try:
        # Create trip planner engine
        engine = TripPlannerEngine(amap_client)
        
        # Output header
        yield {
            "type": "header",
            "text": f"{destination}{days}日游行程规划：\n",
            "data": {
                "destination": destination,
                "days": days,
                "travel_mode": travel_mode,
                "preferences": preferences
            }
        }
        
        # Add preference note if applicable
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
            yield {
                "type": "preference_note",
                "text": f"（已为您优选{pref_text}相关景点）\n",
                "data": {"preferences": preferences}
            }
        
        # Step 1: Search for POIs (not streamed, but fast)
        if preferences:
            pois = await engine._search_pois_by_preference(destination, preferences)
        else:
            pois = await engine._search_attractions(destination)
        
        logger.info(f"Found {len(pois)} POIs for streaming")
        
        if not pois:
            yield {
                "type": "error",
                "text": f"未找到{destination}的景点信息，请尝试其他目的地",
                "data": {"error": "no_attractions_found"}
            }
            return
        
        # Step 2: Cluster POIs by location
        clusters = engine.clusterer.cluster(pois, days, travel_mode)
        
        # Step 3: Allocate to time sessions
        itinerary = engine._allocate_to_sessions(clusters, days)
        
        # Step 4: Estimate transit times
        itinerary = engine._estimate_transit_times(itinerary, travel_mode)
        
        # Step 5: Stream each day's itinerary
        for day_plan in itinerary:
            # Generate theme
            day_plan.theme = engine._generate_theme(day_plan)
            
            # Stream day header
            yield {
                "type": "day_header",
                "text": f"\n第{day_plan.day}天 - {day_plan.theme}\n",
                "data": {
                    "day": day_plan.day,
                    "theme": day_plan.theme
                }
            }
            
            # Stream each session
            for session in day_plan.sessions:
                yield {
                    "type": "session",
                    "text": f"\n{session.period}",
                    "data": {
                        "period": session.period,
                        "stop_count": len(session.stops)
                    }
                }
                
                # Stream each stop
                for stop in session.stops:
                    yield {
                        "type": "stop",
                        "text": f"• [第{stop.order}站] {stop.name}（{stop.address}）",
                        "data": {
                            "order": stop.order,
                            "name": stop.name,
                            "address": stop.address,
                            "location": stop.location,
                            "duration_minutes": stop.duration_minutes
                        }
                    }
                    
                    # Stream transit info if available
                    if stop.transit_to_next:
                        yield {
                            "type": "transit",
                            "text": f"  交通：{stop.transit_to_next.description}",
                            "data": {
                                "mode": stop.transit_to_next.mode,
                                "duration_minutes": stop.transit_to_next.duration_minutes,
                                "description": stop.transit_to_next.description
                            }
                        }
        
        # Step 6: Add dinner recommendations (async, after main itinerary)
        await engine._add_dinner_recommendations(itinerary, destination)
        
        # Stream restaurant recommendations for each day
        for day_plan in itinerary:
            if day_plan.dinner_recommendations:
                yield {
                    "type": "restaurant_header",
                    "text": f"\n第{day_plan.day}天今日精选餐厅",
                    "data": {"day": day_plan.day}
                }
                
                for restaurant in day_plan.dinner_recommendations:
                    yield {
                        "type": "restaurant",
                        "text": f"• {restaurant['name']}",
                        "data": {
                            "name": restaurant['name'],
                            "address": restaurant.get('address', ''),
                            "business_area": restaurant.get('business_area', '')
                        }
                    }
        
        # Complete marker
        yield {
            "type": "complete",
            "text": "",
            "data": {
                "destination": destination,
                "days": days,
                "total_days": len(itinerary)
            }
        }
    
    except Exception as e:
        logger.error(f"Error in streaming plan_trip: {e}", exc_info=True)
        yield {
            "type": "error",
            "text": f"行程规划失败: {str(e)}",
            "data": {"error": str(e)}
        }
