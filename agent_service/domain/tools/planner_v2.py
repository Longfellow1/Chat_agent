"""Enhanced tool planner with location intent support."""

from __future__ import annotations

from typing import Any

from domain.location.intent import LocationIntent
from domain.location.parser import parse_location_intent
from domain.tools.planner import (
    extract_rule_tool_args,
    normalize_tool_args,
    required_slots,
)


def build_tool_plan_v2(
    query: str,
    tool_name: str,
    use_location_intent: bool = True,
) -> dict[str, Any]:
    """Build tool plan with optional location intent support.
    
    Args:
        query: User query (should be rewritten query)
        tool_name: Target tool name
        use_location_intent: Whether to use LocationIntent for find_nearby/plan_trip
        
    Returns:
        Dictionary with tool_name and tool_args
    """
    # For find_nearby: use LocationIntent if enabled
    if tool_name == "find_nearby" and use_location_intent:
        intent = parse_location_intent(query)
        
        # Check completeness
        if not intent.is_complete():
            return {
                "tool_name": tool_name,
                "tool_args": {},
                "missing_slots": ["city"],
                "error": "incomplete_intent",
                "intent": intent.to_dict(),
            }
        
        return {
            "tool_name": tool_name,
            "tool_args": intent.to_tool_args(),
            "missing_slots": [],
            "intent": intent.to_dict(),
            "confidence": intent.confidence,
        }
    
    # For other tools: use existing planner
    tool_args = extract_rule_tool_args(query, tool_name)
    normalized = normalize_tool_args(tool_name, tool_args, query)
    
    # Check required slots
    required = required_slots(tool_name)
    missing = [k for k in required if not str(normalized.get(k, "")).strip()]
    
    return {
        "tool_name": tool_name,
        "tool_args": normalized,
        "missing_slots": missing,
    }


def extract_location_intent(query: str) -> LocationIntent:
    """Extract location intent from query.
    
    Convenience function for direct access to LocationIntent parsing.
    """
    return parse_location_intent(query)
