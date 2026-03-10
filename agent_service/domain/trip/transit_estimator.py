"""Transit time estimation module."""

import math
from typing import Dict, Optional
from .schema import TransitInfo


class TransitTimeEstimator:
    """Estimates transit time between POIs based on geographic data."""
    
    def estimate(
        self,
        poi_a: Dict,
        poi_b: Dict,
        mode: str = "transit"
    ) -> TransitInfo:
        """
        Estimate transit time between two POIs.
        
        Args:
            poi_a: Starting POI with location, business_area, district, adcode
            poi_b: Ending POI with location, business_area, district, adcode
            mode: Travel mode ("transit" or "driving")
        
        Returns:
            TransitInfo with duration and description
        """
        # Check if we have enough data for estimation
        has_location_a = bool(poi_a.get("location"))
        has_location_b = bool(poi_b.get("location"))
        has_business_area_a = bool(poi_a.get("business_area"))
        has_business_area_b = bool(poi_b.get("business_area"))
        has_district_a = bool(poi_a.get("district"))
        has_district_b = bool(poi_b.get("district"))
        has_adcode_a = bool(poi_a.get("adcode"))
        has_adcode_b = bool(poi_a.get("adcode"))
        
        # If missing critical fields, return conservative estimate
        if not (has_location_a and has_location_b) and \
           not (has_business_area_a and has_business_area_b) and \
           not (has_district_a and has_district_b) and \
           not (has_adcode_a and has_adcode_b):
            return self._conservative_estimate(mode)
        
        # Same business area
        if poi_a.get("business_area") and poi_a.get("business_area") == poi_b.get("business_area"):
            return self._same_business_area(mode)
        
        # Same district, different business area
        if poi_a.get("district") and poi_a.get("district") == poi_b.get("district"):
            return self._same_district(mode)
        
        # Check adcode for same city (first 2 digits match for 6-digit codes)
        adcode_a = poi_a.get("adcode") or ""
        adcode_b = poi_b.get("adcode") or ""
        
        if len(adcode_a) == 6 and len(adcode_b) == 6 and adcode_a[:2] == adcode_b[:2]:
            # Same city, cross district
            return self._cross_district(poi_a, poi_b, mode)
        
        # If we have location data, calculate distance
        if has_location_a and has_location_b:
            return self._cross_city(poi_a, poi_b, mode)
        
        # Otherwise, return conservative estimate
        return self._conservative_estimate(mode)
    
    def _same_business_area(self, mode: str) -> TransitInfo:
        """Estimate time within same business area."""
        if mode == "transit":
            return TransitInfo(
                mode="transit",
                duration_minutes=12,
                description="步行或公交约12分钟"
            )
        else:
            return TransitInfo(
                mode="driving",
                duration_minutes=8,
                distance_km=1.5,
                description="驾车约8分钟"
            )
    
    def _conservative_estimate(self, mode: str) -> TransitInfo:
        """Conservative estimate when data is insufficient."""
        if mode == "transit":
            return TransitInfo(
                mode="transit",
                duration_minutes=30,
                description="建议预留30分钟"
            )
        else:
            return TransitInfo(
                mode="driving",
                duration_minutes=20,
                description="建议预留20分钟"
            )
    
    def _same_district(self, mode: str) -> TransitInfo:
        """Estimate time within same district, different business areas."""
        if mode == "transit":
            return TransitInfo(
                mode="transit",
                duration_minutes=25,
                description="公交或地铁约25分钟"
            )
        else:
            return TransitInfo(
                mode="driving",
                duration_minutes=18,
                distance_km=5.0,
                description="驾车约18分钟"
            )
    
    def _cross_district(self, poi_a: Dict, poi_b: Dict, mode: str) -> TransitInfo:
        """Estimate time across districts within same city."""
        # Check if same district (first 4 digits of adcode match)
        adcode_a = poi_a.get("adcode") or ""
        adcode_b = poi_b.get("adcode") or ""
        
        # If adcodes are 6 digits and first 4 match, they're in same district
        if len(adcode_a) == 6 and len(adcode_b) == 6:
            if adcode_a[:4] == adcode_b[:4]:
                # Same district, different business area
                return self._same_district(mode)
        
        # Cross district within same city (first 2 digits match)
        if mode == "transit":
            return TransitInfo(
                mode="transit",
                duration_minutes=50,
                description="地铁约50分钟"
            )
        else:
            return TransitInfo(
                mode="driving",
                duration_minutes=38,
                distance_km=15.0,
                description="驾车约38分钟"
            )
    
    def _cross_city(self, poi_a: Dict, poi_b: Dict, mode: str) -> TransitInfo:
        """Estimate time across cities."""
        # Calculate straight-line distance
        distance_km = self._calculate_distance(
            poi_a.get("location", ""),
            poi_b.get("location", "")
        )
        
        if mode == "transit":
            # High-speed rail: ~200km/h
            duration = int(distance_km / 200 * 60)
            return TransitInfo(
                mode="transit",
                duration_minutes=max(duration, 60),  # At least 1 hour
                distance_km=distance_km,
                description=f"高铁约{duration}分钟"
            )
        else:
            # Highway: ~80km/h
            duration = int(distance_km / 80 * 60)
            return TransitInfo(
                mode="driving",
                duration_minutes=max(duration, 30),  # At least 30 minutes
                distance_km=distance_km,
                description=f"驾车约{duration}分钟"
            )
    
    def _calculate_distance(self, loc_a: str, loc_b: str) -> float:
        """
        Calculate straight-line distance between two locations.
        
        Args:
            loc_a: "lng,lat" format
            loc_b: "lng,lat" format
        
        Returns:
            Distance in kilometers
        """
        try:
            lng1, lat1 = map(float, loc_a.split(","))
            lng2, lat2 = map(float, loc_b.split(","))
            
            # Haversine formula
            R = 6371  # Earth radius in km
            
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlng / 2) ** 2)
            
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
        except (ValueError, AttributeError):
            # Default to 10km if parsing fails
            return 10.0
