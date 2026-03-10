"""POI clustering module for trip planning."""

from typing import List, Dict


class POIClusterer:
    """Clusters POIs by geographic location for trip planning."""
    
    def cluster(
        self,
        pois: List[Dict],
        days: int,
        travel_mode: str = "transit"
    ) -> List[List[Dict]]:
        """
        Cluster POIs into daily groups.
        
        Args:
            pois: List of POI dictionaries
            days: Number of days to plan
            travel_mode: Travel mode ("transit" or "driving")
        
        Returns:
            List of POI lists, one per day
        """
        if not pois:
            return [[] for _ in range(days)]
        
        # Different clustering strategies based on travel mode
        if travel_mode == "driving":
            # Driving: can cross districts, optimize by route
            clusters = self._cluster_by_route(pois)
        else:
            # Transit: prefer same district/metro line
            clusters = self._cluster_by_business_area(pois)
        
        # Allocate clusters to days
        daily_clusters = self._allocate_to_days(clusters, days)
        
        return daily_clusters
    
    def _cluster_by_business_area(self, pois: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group POIs by business area.
        
        Args:
            pois: List of POI dictionaries
        
        Returns:
            Dictionary mapping business_area to list of POIs
        """
        clusters = {}
        
        for poi in pois:
            area = poi.get("business_area") or poi.get("district") or "其他"
            if area not in clusters:
                clusters[area] = []
            clusters[area].append(poi)
        
        return clusters
    
    def _allocate_to_days(
        self,
        clusters: Dict[str, List[Dict]],
        days: int
    ) -> List[List[Dict]]:
        """
        Allocate clustered POIs to days.
        
        Args:
            clusters: Dictionary of business_area -> POIs
            days: Number of days
        
        Returns:
            List of POI lists, one per day
        """
        # Flatten all POIs
        all_pois = []
        for area, pois in clusters.items():
            all_pois.extend(pois)
        
        # Allocate ~5 POIs per day
        pois_per_day = 5
        daily_clusters = []
        
        for i in range(days):
            start = i * pois_per_day
            end = start + pois_per_day
            daily_pois = all_pois[start:end]
            daily_clusters.append(daily_pois)
        
        return daily_clusters
    
    def _cluster_by_route(self, pois: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Cluster POIs by route optimization (for driving mode).
        
        For now, use simple geographic grouping.
        Future: implement TSP-like route optimization.
        
        Args:
            pois: List of POI dictionaries
        
        Returns:
            Dictionary mapping route_id to list of POIs
        """
        # Simple implementation: group by district
        clusters = {}
        
        for poi in pois:
            district = poi.get("district") or "其他"
            if district not in clusters:
                clusters[district] = []
            clusters[district].append(poi)
        
        return clusters
