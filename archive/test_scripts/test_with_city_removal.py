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

# 模拟完整流程
query = '我在天津天河，哪里有加油站'
q = re.sub(r'[\s，,。.!?？；;、]+', '', query)
print(f'q: {q}')

# 移除城市
extracted_city = '天津'
q_clean = q
if extracted_city:
    city_base = extracted_city.replace("市", "")
    q_clean = q_clean.replace(extracted_city, "").replace(city_base, "")
print(f'q_clean (after city removal): {q_clean}')

# Priority 3
q_for_near = re.sub(r'^(我在|在|我去|去|我到|到|帮我找|找|帮我|给我)', '', q_clean)
print(f'q_for_near: {q_for_near}')

near_pattern = r'([\u4e00-\u9fa5A-Za-z0-9]{2,20})(附近|周边|旁边|周围|一带|哪里)'
match = re.search(near_pattern, q_for_near)
if match:
    region = match.group(1)
    print(f'Matched region: {region}')
    region = _clean_anchor_region(region)
    print(f'Cleaned region: {region}')
