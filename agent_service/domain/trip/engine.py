"""Trip planner engine - core logic for trip planning."""

import logging
from typing import List, Dict, Optional

from .schema import TripItinerary, DayPlan, Session, Stop, TransitInfo
from .clusterer import POIClusterer
from .transit_estimator import TransitTimeEstimator

logger = logging.getLogger(__name__)


# M5.2: 偏好到关键词的映射（每个偏好只用一个主关键词，控制API调用量）
PREFERENCE_PRIMARY_KEYWORD = {
    "food": "美食餐厅",
    "entertainment": "娱乐场所",
    "culture": "博物馆景区",
    "nature": "公园风景区",
    "shopping": "购物中心",
    "relax": "休闲会所",
}


class TripPlannerEngine:
    """Core engine for trip planning."""
    
    def __init__(self, amap_client):
        """
        Initialize trip planner engine.
        
        Args:
            amap_client: AmapMCPClient instance for POI search
        """
        self.amap = amap_client
        self.clusterer = POIClusterer()
        self.transit_estimator = TransitTimeEstimator()
    
    async def plan(
        self,
        destination: str,
        days: int,
        travel_mode: str = "transit",
        user_prefs: Optional[List[str]] = None
    ) -> TripItinerary:
        """
        Plan a trip itinerary.
        
        Args:
            destination: Destination city
            days: Number of days
            travel_mode: Travel mode ("transit" or "driving")
            user_prefs: User preferences list (M5.2: ["food", "entertainment", etc.])
        
        Returns:
            TripItinerary object
        """
        logger.info(f"Planning {days}-day trip to {destination}, mode={travel_mode}, prefs={user_prefs}")
        
        # Step 1: Search for attractions (根据偏好调整)
        if user_prefs:
            # M5.2: 有偏好，根据偏好搜索POI
            pois = await self._search_pois_by_preference(destination, user_prefs)
        else:
            # M5.1: 无偏好，搜索综合景点
            pois = await self._search_attractions(destination)
        
        logger.info(f"Found {len(pois)} POIs")
        
        if not pois:
            # Return empty itinerary if no POIs found
            return TripItinerary(
                destination=destination,
                days=days,
                travel_mode=travel_mode,
                itinerary=[]
            )
        
        # Step 2: Cluster POIs by location
        clusters = self.clusterer.cluster(pois, days, travel_mode)
        logger.info(f"Clustered into {len(clusters)} days")
        
        # Step 3: Allocate to time sessions
        itinerary = self._allocate_to_sessions(clusters, days)
        
        # Step 4: Estimate transit times
        itinerary = self._estimate_transit_times(itinerary, travel_mode)
        
        # Step 5: Add dinner recommendations (M5.1)
        await self._add_dinner_recommendations(itinerary, destination)
        
        # Step 6: Generate themes
        for day_plan in itinerary:
            day_plan.theme = self._generate_theme(day_plan)
        
        return TripItinerary(
            destination=destination,
            days=days,
            travel_mode=travel_mode,
            itinerary=itinerary
        )
    
    async def _search_attractions(self, city: str) -> List[Dict]:
        """
        Search for attractions in the city.
        
        Args:
            city: City name
        
        Returns:
            List of POI dictionaries
        """
        try:
            # Call Amap MCP call_tool with maps_text_search
            result = await self.amap.call_tool_async(
                "maps_text_search",
                {
                    "keywords": f"{city} 景点",
                    "city": city,
                    "types": "110000|120000|130000",  # Attraction types
                    "offset": 20
                }
            )
            
            # Parse result from MCP response
            content = result.get("content", [])
            if not content:
                logger.warning(f"No content in MCP response for {city}")
                return []
            
            # Extract POIs from content
            pois_text = content[0].get("text", "")
            import json
            pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
            pois_list = pois_data.get("pois", [])
            
            pois = []
            for poi in pois_list:
                # Get location, use empty string if not available
                # Note: Amap MCP text_search may not return location field
                location = poi.get("location", "")
                    
                pois.append({
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": location,  # May be empty
                    "business_area": poi.get("business_area"),
                    "district": poi.get("district"),
                    "adcode": poi.get("adcode"),
                    "type": poi.get("type"),
                    "typecode": poi.get("typecode"),
                })
            
            return pois[:15]  # Return top 15
            
        except Exception as e:
            logger.error(f"Error searching attractions: {e}")
            return []
    
    async def _search_pois_by_preference(self, city: str, preferences: List[str]) -> List[Dict]:
        """
        Search for POIs based on user preferences (M5.2).
        
        API调用量控制：每个偏好只调用1次find_nearby，使用主关键词
        
        Args:
            city: City name
            preferences: List of preference types (e.g., ["food", "entertainment"])
        
        Returns:
            List of POI dictionaries
        """
        all_pois = []
        
        for pref in preferences:
            # 每个偏好只调用一次，使用主关键词
            keyword = PREFERENCE_PRIMARY_KEYWORD.get(pref)
            if not keyword:
                logger.warning(f"Unknown preference type: {pref}")
                continue
            
            try:
                # Call Amap MCP with preference keyword
                result = await self.amap.call_tool_async(
                    "maps_text_search",
                    {
                        "keywords": keyword,
                        "city": city,
                        "offset": 20
                    }
                )
                
                # Parse result
                content = result.get("content", [])
                if not content:
                    logger.warning(f"No content for preference {pref} in {city}")
                    continue
                
                pois_text = content[0].get("text", "")
                import json
                pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
                pois_list = pois_data.get("pois", [])
                
                for poi in pois_list:
                    all_pois.append({
                        "name": poi.get("name", ""),
                        "address": poi.get("address", ""),
                        "location": poi.get("location", ""),
                        "business_area": poi.get("business_area"),
                        "district": poi.get("district"),
                        "adcode": poi.get("adcode"),
                        "type": poi.get("type"),
                        "typecode": poi.get("typecode"),
                        "preference": pref,  # 标记偏好类型
                    })
                
                logger.info(f"Found {len(pois_list)} POIs for preference '{pref}' in {city}")
                
            except Exception as e:
                logger.error(f"Error searching POIs for preference {pref}: {e}")
        
        # 返回前15个（去重）
        seen = set()
        unique_pois = []
        for poi in all_pois:
            key = (poi["name"], poi.get("address", ""))
            if key not in seen:
                seen.add(key)
                unique_pois.append(poi)
        
        return unique_pois[:15]
    
    def _allocate_to_sessions(
        self,
        clusters: List[List[Dict]],
        days: int
    ) -> List[DayPlan]:
        """
        Allocate POIs to time sessions (上午/下午/晚上) based on duration.
        
        Args:
            clusters: List of POI lists, one per day
            days: Number of days
        
        Returns:
            List of DayPlan objects
        """
        itinerary = []
        
        # Time budgets for each session (in minutes)
        MORNING_BUDGET = 240  # 4 hours
        AFTERNOON_BUDGET = 240  # 4 hours
        EVENING_BUDGET = 120  # 2 hours
        
        for day_idx, cluster in enumerate(clusters):
            if not cluster:
                continue
            
            day_plan = DayPlan(
                day=day_idx + 1,
                theme="",  # Will be generated later
                sessions=[]
            )
            
            # Allocate POIs to sessions based on cumulative duration
            morning_pois = []
            afternoon_pois = []
            evening_pois = []
            
            morning_time = 0
            afternoon_time = 0
            evening_time = 0
            
            for poi in cluster:
                # Default duration: 120 minutes
                duration = poi.get("recommended_duration_minutes", 120)
                
                # Try to fit into morning first
                if morning_time + duration <= MORNING_BUDGET:
                    morning_pois.append(poi)
                    morning_time += duration
                # Then afternoon
                elif afternoon_time + duration <= AFTERNOON_BUDGET:
                    afternoon_pois.append(poi)
                    afternoon_time += duration
                # Finally evening
                elif evening_time + duration <= EVENING_BUDGET:
                    evening_pois.append(poi)
                    evening_time += duration
                # Skip if no time left
            
            if morning_pois:
                day_plan.sessions.append(Session(
                    period="上午",
                    stops=self._format_stops(morning_pois, 1)
                ))
            
            if afternoon_pois:
                start_order = len(morning_pois) + 1
                day_plan.sessions.append(Session(
                    period="下午",
                    stops=self._format_stops(afternoon_pois, start_order)
                ))
            
            if evening_pois:
                start_order = len(morning_pois) + len(afternoon_pois) + 1
                day_plan.sessions.append(Session(
                    period="晚上",
                    stops=self._format_stops(evening_pois, start_order)
                ))
            
            itinerary.append(day_plan)
        
        return itinerary
    
    def _format_stops(self, pois: List[Dict], start_order: int) -> List[Stop]:
        """
        Format POIs as Stop objects.
        
        Args:
            pois: List of POI dictionaries
            start_order: Starting order number
        
        Returns:
            List of Stop objects
        """
        stops = []
        for idx, poi in enumerate(pois):
            stop = Stop(
                order=start_order + idx,
                type="景点",
                name=poi.get("name", ""),
                address=poi.get("address", ""),
                location=poi.get("location", ""),
                duration_minutes=120,  # Default 2 hours
                business_area=poi.get("business_area"),
                district=poi.get("district"),
                adcode=poi.get("adcode"),
            )
            stops.append(stop)
        
        return stops
    
    def _estimate_transit_times(
        self,
        itinerary: List[DayPlan],
        travel_mode: str
    ) -> List[DayPlan]:
        """
        Estimate transit times between stops.
        
        Args:
            itinerary: List of DayPlan objects
            travel_mode: Travel mode
        
        Returns:
            Updated itinerary with transit times
        """
        for day_plan in itinerary:
            all_stops = []
            for session in day_plan.sessions:
                all_stops.extend(session.stops)
            
            # Estimate transit time between consecutive stops
            for i in range(len(all_stops) - 1):
                stop_a = all_stops[i]
                stop_b = all_stops[i + 1]
                
                poi_a = {
                    "location": stop_a.location,
                    "business_area": stop_a.business_area,
                    "district": stop_a.district,
                    "adcode": stop_a.adcode,
                }
                poi_b = {
                    "location": stop_b.location,
                    "business_area": stop_b.business_area,
                    "district": stop_b.district,
                    "adcode": stop_b.adcode,
                }
                
                transit_info = self.transit_estimator.estimate(
                    poi_a, poi_b, travel_mode
                )
                stop_a.transit_to_next = transit_info
        
        return itinerary
    
    def _generate_theme(self, day_plan: DayPlan) -> str:
        """
        Generate a theme for the day based on POIs.
        
        Args:
            day_plan: DayPlan object
        
        Returns:
            Theme string
        """
        # Simple theme generation based on day number
        themes = [
            "经典地标游",
            "文化艺术游",
            "自然风光游",
            "美食探索游",
            "历史古迹游",
        ]
        
        return themes[(day_plan.day - 1) % len(themes)]
    
    async def _add_dinner_recommendations(
        self,
        itinerary: List[DayPlan],
        city: str
    ) -> None:
        """
        Add dinner recommendations for each day (M5.1).
        
        Strategy: Single city-wide restaurant search, reuse for all days.
        This avoids exceeding API call limits (8 calls max).
        
        Args:
            itinerary: List of DayPlan objects
            city: City name
        """
        # Get city-wide high-rated restaurants (single API call)
        restaurants = await self._get_city_restaurants(city)
        
        if not restaurants:
            logger.warning(f"No restaurants found in {city}")
            return
        
        # For each day, recommend restaurants near the last stop
        for day_plan in itinerary:
            # Find the last stop of the day (遍历所有session找最后一个stop)
            last_stop = None
            for session in day_plan.sessions:
                if session.stops:
                    last_stop = session.stops[-1]
            
            if not last_stop:
                logger.warning(f"Day {day_plan.day}: No stops found")
                # Still provide city-wide recommendations
                day_plan.dinner_recommendations = restaurants[:3]
                continue
            
            # Filter restaurants near the last stop
            # Use business_area or district for matching (location field may be missing)
            nearby_restaurants = []
            for restaurant in restaurants:
                # Prefer same business_area, fallback to same district
                if (last_stop.business_area and 
                    restaurant.get("business_area") == last_stop.business_area):
                    nearby_restaurants.append(restaurant)
                elif (last_stop.district and 
                      restaurant.get("district") == last_stop.district):
                    nearby_restaurants.append(restaurant)
            
            # If no nearby restaurants, use top 3 from city-wide list
            if not nearby_restaurants:
                nearby_restaurants = restaurants[:3]
            
            # Take top 3 restaurants
            day_plan.dinner_recommendations = nearby_restaurants[:3]
            logger.info(f"Day {day_plan.day}: Added {len(day_plan.dinner_recommendations)} dinner recommendations")
    
    async def _get_city_restaurants(self, city: str) -> List[Dict]:
        """
        Get high-rated restaurants in the city (single API call).
        
        Args:
            city: City name
        
        Returns:
            List of restaurant dictionaries
        """
        try:
            # Call Amap MCP with restaurant keywords
            result = await self.amap.call_tool_async(
                "maps_text_search",
                {
                    "keywords": "美食餐厅",
                    "city": city,
                    "types": "050000|060000",  # Restaurant types
                    "offset": 20
                }
            )
            
            # Parse result
            content = result.get("content", [])
            if not content:
                logger.warning(f"No content in MCP response for restaurants in {city}")
                return []
            
            pois_text = content[0].get("text", "")
            import json
            pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
            pois_list = pois_data.get("pois", [])
            
            restaurants = []
            for poi in pois_list:
                restaurants.append({
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": poi.get("location", ""),
                    "business_area": poi.get("business_area"),
                    "district": poi.get("district"),
                    "adcode": poi.get("adcode"),
                    "type": poi.get("type"),
                })
            
            return restaurants[:15]  # Return top 15
            
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []
