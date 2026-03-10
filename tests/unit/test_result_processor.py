"""Tests for result processor (rerank and filter)."""

import pytest

from agent_service.domain.location.intent import LocationIntent, SortBy
from agent_service.domain.location.result_processor import (
    BrandFilter,
    CategoryFilter,
    DistanceSorter,
    Open24hFilter,
    PriceSorter,
    RatingSorter,
    ResultProcessorChain,
    TopNSelector,
    create_default_processor_chain,
)


@pytest.fixture
def sample_pois():
    """Sample POI results for testing."""
    return [
        {
            "name": "7-11便利店(鸟巢店)",
            "type": "购物服务;便利店",
            "distance": "500",
            "rating": "4.5",
            "price": "15",
        },
        {
            "name": "全家便利店",
            "type": "购物服务;便利店",
            "distance": "300",
            "rating": "4.8",
            "price": "18",
        },
        {
            "name": "罗森便利店",
            "type": "购物服务;便利店",
            "distance": "800",
            "rating": "4.6",
            "price": "16",
        },
        {
            "name": "国家体育场",
            "type": "体育休闲服务;体育场馆",
            "distance": "100",
            "rating": "4.9",
        },
    ]


def test_brand_filter():
    """Test brand filter."""
    pois = [
        {"name": "7-11便利店", "type": "便利店"},
        {"name": "全家便利店", "type": "便利店"},
        {"name": "罗森便利店", "type": "便利店"},
    ]
    
    intent = LocationIntent(brand="7-11")
    filter_processor = BrandFilter()
    
    result = filter_processor.process(pois, intent)
    
    assert len(result) == 1
    assert "7-11" in result[0]["name"]


def test_category_filter():
    """Test category filter."""
    pois = [
        {"name": "7-11便利店", "type": "购物服务;便利店"},
        {"name": "国家体育场", "type": "体育休闲服务;体育场馆"},
    ]
    
    intent = LocationIntent(category="便利店")
    filter_processor = CategoryFilter()
    
    result = filter_processor.process(pois, intent)
    
    assert len(result) == 1
    assert "便利店" in result[0]["type"]


def test_distance_sorter_asc(sample_pois):
    """Test distance sorter (ascending)."""
    intent = LocationIntent(sort_by=SortBy.DISTANCE, sort_order="asc")
    sorter = DistanceSorter()
    
    result = sorter.process(sample_pois, intent)
    
    # Should be sorted by distance: 100 < 300 < 500 < 800
    distances = [float(r["distance"]) for r in result]
    assert distances == sorted(distances)
    assert result[0]["name"] == "国家体育场"  # Closest


def test_distance_sorter_desc(sample_pois):
    """Test distance sorter (descending)."""
    intent = LocationIntent(sort_by=SortBy.DISTANCE, sort_order="desc")
    sorter = DistanceSorter()
    
    result = sorter.process(sample_pois, intent)
    
    # Should be sorted by distance: 800 > 500 > 300 > 100
    distances = [float(r["distance"]) for r in result]
    assert distances == sorted(distances, reverse=True)
    assert result[0]["name"] == "罗森便利店"  # Farthest


def test_rating_sorter(sample_pois):
    """Test rating sorter."""
    intent = LocationIntent(sort_by=SortBy.RATING, sort_order="desc")
    sorter = RatingSorter()
    
    result = sorter.process(sample_pois, intent)
    
    # Should be sorted by rating: 4.9 > 4.8 > 4.6 > 4.5
    ratings = [float(r["rating"]) for r in result]
    assert ratings == sorted(ratings, reverse=True)
    assert result[0]["name"] == "国家体育场"  # Highest rating


def test_price_sorter(sample_pois):
    """Test price sorter."""
    intent = LocationIntent(sort_by=SortBy.PRICE, sort_order="asc")
    sorter = PriceSorter()
    
    result = sorter.process(sample_pois, intent)
    
    # Should be sorted by price: 15 < 16 < 18
    # Note: 国家体育场 has no price, should be at the end
    prices = [float(r.get("price", 999999)) for r in result]
    assert prices == sorted(prices)


def test_top_n_selector(sample_pois):
    """Test top N selector."""
    intent = LocationIntent()
    intent.limit = 2
    
    selector = TopNSelector()
    result = selector.process(sample_pois, intent)
    
    assert len(result) == 2


def test_processor_chain_brand_and_distance(sample_pois):
    """Test processor chain: filter by brand, then sort by distance."""
    intent = LocationIntent(
        brand="便利店",
        sort_by=SortBy.DISTANCE,
        sort_order="asc"
    )
    
    chain = ResultProcessorChain()
    chain.register(BrandFilter())
    chain.register(DistanceSorter())
    
    result = chain.process(sample_pois, intent)
    
    # Should filter out 国家体育场, then sort by distance
    assert len(result) == 3
    assert all("便利店" in r["name"] for r in result)
    
    # Check distance order
    distances = [float(r["distance"]) for r in result]
    assert distances == sorted(distances)


def test_processor_chain_category_and_rating(sample_pois):
    """Test processor chain: filter by category, then sort by rating."""
    intent = LocationIntent(
        category="便利店",
        sort_by=SortBy.RATING,
        sort_order="desc"
    )
    
    chain = ResultProcessorChain()
    chain.register(CategoryFilter())
    chain.register(RatingSorter())
    
    result = chain.process(sample_pois, intent)
    
    # Should filter to only convenience stores, then sort by rating
    assert len(result) == 3
    assert all("便利店" in r["type"] for r in result)
    
    # Check rating order (descending)
    ratings = [float(r["rating"]) for r in result]
    assert ratings == sorted(ratings, reverse=True)
    assert result[0]["name"] == "全家便利店"  # Highest rating among convenience stores


def test_default_processor_chain(sample_pois):
    """Test default processor chain."""
    intent = LocationIntent(
        brand="便利店",
        sort_by=SortBy.DISTANCE,
        sort_order="asc"
    )
    
    chain = create_default_processor_chain()
    result = chain.process(sample_pois, intent)
    
    # Should filter by brand, sort by distance, and limit to top 5
    assert len(result) <= 5
    assert all("便利店" in r["name"] for r in result)


def test_real_world_scenario_nearest_711(sample_pois):
    """Test real-world scenario: 最近的711."""
    # Modify sample data to include 711
    pois = [
        {"name": "7-11便利店(鸟巢店)", "type": "便利店", "distance": "500"},
        {"name": "全家便利店", "type": "便利店", "distance": "300"},
        {"name": "7-11便利店(朝阳店)", "type": "便利店", "distance": "200"},
        {"name": "国家体育场", "type": "体育场馆", "distance": "100"},
    ]
    
    intent = LocationIntent(
        brand="7-11",
        sort_by=SortBy.DISTANCE,
        sort_order="asc"
    )
    
    chain = create_default_processor_chain()
    result = chain.process(pois, intent)
    
    # Should filter to only 7-11, sort by distance
    assert len(result) == 2
    assert all("7-11" in r["name"] for r in result)
    assert result[0]["name"] == "7-11便利店(朝阳店)"  # Nearest 7-11


def test_empty_results():
    """Test handling of empty results."""
    pois = []
    intent = LocationIntent(brand="711")
    
    chain = create_default_processor_chain()
    result = chain.process(pois, intent)
    
    assert result == []


def test_no_matching_brand():
    """Test when no results match the brand filter."""
    pois = [
        {"name": "全家便利店", "type": "便利店"},
        {"name": "罗森便利店", "type": "便利店"},
    ]
    
    intent = LocationIntent(brand="7-11")
    
    chain = ResultProcessorChain()
    chain.register(BrandFilter())
    
    result = chain.process(pois, intent)
    
    assert result == []
