#!/usr/bin/env python3
import sys
sys.path.insert(0, 'agent_service')

from agent_service.domain.intents.router_4b_with_logprobs import RuleBasedRouter

# 测试"GAI是谁"
result = RuleBasedRouter.try_route("GAI是谁")
print(f"Query: GAI是谁")
print(f"Result: {result}")
print(f"Tool: {result.tool.value if result else None}")
