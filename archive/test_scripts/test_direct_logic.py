import re

def _clean_anchor_region(region: str) -> str:
    if not region:
        return ""
    
    region = re.sub(
        r'^(?:'
        r'请|麻烦|帮忙|帮我找|帮我|给我|帮我一下|给我一下|'
        r'推荐|推荐一下|求推荐|'
        r'建议|建议一下|'
        r'查一下|搜一下|找一下|找|搜索|查找|查询|'
        r'我要|我想|想要|需要|想|'
        r'在|去|到|从|来'
        r')',
        '',
        region
    )
    
    region = re.sub(r'(哪里|这里|那边|附近|周边|旁边|周围|一带)$', '', region)
    region = region.rstrip("的")
    
    return region.strip()

# 测试新逻辑
q_clean = '我在天津天河哪里有加油站'
q_for_near = re.sub(r'^(我在|在|我去|去|我到|到|帮我找|找|帮我|给我)', '', q_clean)
print(f'q_clean: {q_clean}')
print(f'q_for_near: {q_for_near}')

near_pattern = r'([\u4e00-\u9fa5A-Za-z0-9]{2,20})(附近|周边|旁边|周围|一带|哪里)'
match = re.search(near_pattern, q_for_near)
if match:
    region = match.group(1)
    print(f'Matched region: {region}')
    region = _clean_anchor_region(region)
    print(f'Cleaned region: {region}')
