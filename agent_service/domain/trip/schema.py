"""Data schemas for trip planning."""

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class TransitInfo:
    """Transit information between stops."""
    mode: str  # "transit" or "driving"
    duration_minutes: int
    distance_km: Optional[float] = None
    description: str = ""


@dataclass
class Stop:
    """A stop in the itinerary (POI or restaurant)."""
    order: int
    type: str  # "景点" or "餐厅"
    name: str
    address: str
    location: str  # "lng,lat"
    duration_minutes: int = 120
    recommended_duration_minutes: int = 120  # 推荐游览时长
    transit_to_next: Optional[TransitInfo] = None
    business_area: Optional[str] = None
    district: Optional[str] = None
    adcode: Optional[str] = None


@dataclass
class Session:
    """A time session in a day (上午/下午/晚上)."""
    period: str  # "上午", "下午", "晚上"
    stops: List[Stop]


@dataclass
class DayPlan:
    """Plan for one day."""
    day: int
    theme: str
    sessions: List[Session]
    dinner_recommendations: Optional[List[Dict]] = None  # M5.1: 晚餐推荐


@dataclass
class TripItinerary:
    """Complete trip itinerary."""
    destination: str
    days: int
    travel_mode: str  # "transit" or "driving"
    itinerary: List[DayPlan]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "destination": self.destination,
            "days": self.days,
            "travel_mode": self.travel_mode,
            "itinerary": [
                {
                    "day": day.day,
                    "theme": day.theme,
                    "sessions": [
                        {
                            "period": session.period,
                            "stops": [
                                {
                                    "order": stop.order,
                                    "type": stop.type,
                                    "name": stop.name,
                                    "address": stop.address,
                                    "location": stop.location,
                                    "duration_minutes": stop.duration_minutes,
                                    "transit_to_next": {
                                        "mode": stop.transit_to_next.mode,
                                        "duration_minutes": stop.transit_to_next.duration_minutes,
                                        "distance_km": stop.transit_to_next.distance_km,
                                        "description": stop.transit_to_next.description,
                                    } if stop.transit_to_next else None,
                                }
                                for stop in session.stops
                            ],
                        }
                        for session in day.sessions
                    ],
                    "dinner_recommendations": day.dinner_recommendations,
                }
                for day in self.itinerary
            ],
        }
