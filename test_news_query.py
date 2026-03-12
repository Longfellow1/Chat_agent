#!/usr/bin/env python3
import sys
sys.path.insert(0, 'agent_service')

from agent_service.domain.intents.router_4b_with_logprobs import RuleBasedRouter

test_cases = [
    "最近有什么国际局势热点",
    "最近有什么大事",
    "今天有什么新闻",
]

for query in test_cases:
    result = RuleBasedRouter.try_route(query)
    tool = result.tool.value if result else None
    print(f"Query: {query}")
    print(f"Tool: {tool}\n")
