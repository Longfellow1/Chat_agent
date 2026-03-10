# M5.4 plan_trip M5 功能增强规划

## 背景

M4完成基础行程规划功能后，用户反馈需要更丰富的内容：
- 美食推荐
- 娱乐推荐
- 休闲推荐

## M5功能增强

### 1. 默认餐厅推荐 ⭐

**需求**:
- 当用户不提出偏好时，默认推荐每天晚上游览点附近的高分餐厅
- 提升用户体验，解决"去哪吃"的高频需求

**实现方案**:
```python
# 在engine.py的plan()方法中
for day_plan in itinerary:
    # 获取当天行程结束时用户所在的位置
    # 遍历所有session，找到最后一个stop
    last_stop = None
    for session in day_plan.sessions:
        if session.stops:
            last_stop = session.stops[-1]
    
    # 如果当天有景点安排，查询附近餐厅
    if last_stop:
        restaurants = amap_client.find_nearby(
            keyword="餐厅",
            location=last_stop.location,
            city=destination
        )
        
        # 筛选高分餐厅（评分>4.0）
        high_rated = [r for r in restaurants if r.get("rating", 0) >= 4.0]
        
        # 添加到day_plan
        day_plan.dinner_recommendations = high_rated[:3]
```

**LLM重写调整**:
```python
system_prompt = """...
输出格式：
第1天：上午游览A、B，下午前往C。
晚餐推荐：D餐厅、E餐厅（{last_stop}附近）
"""
```

**优先级**: P1（高频需求）

**注意**: 这是默认行为，用户没有提出偏好时触发。与"美食偏好"场景不同。

---

### 2. 用户偏好参数支持

**需求**:
- 支持用户指定偏好：美食、娱乐、休闲、文化、自然等
- 根据偏好调整景点选择和推荐
- 与默认餐厅推荐不同，偏好会影响景点本身的选择

**场景区分**:

#### 场景1: 默认餐厅推荐（无偏好）
- 用户查询："帮我规划上海2日游"
- 行为：正常规划景点 + 晚上推荐餐厅
- 景点类型：综合（地标、文化、自然等）

#### 场景2: 美食偏好
- 用户查询："帮我规划一个吃吃吃的上海2日游"
- 行为：景点本身偏向餐厅和小吃街 + 晚上推荐餐厅
- 景点类型：美食街、特色餐厅、小吃聚集地

**实现方案**:

```python
# 参数扩展
def plan_trip(
    destination: str,
    days: int = 2,
    travel_mode: str = "transit",
    preferences: list[str] = None,  # 新增：["food", "entertainment", "culture"]
    amap_client: AmapMCPClient | None = None
) -> ToolResult:
    ...
```

**偏好关键词映射表**:
```python
# 在trip_router.py中
PREFERENCE_SIGNALS = {
    "food": ["美食", "吃", "餐厅", "小吃", "吃吃吃", "品尝"],
    "entertainment": ["娱乐", "玩", "酒吧", "夜生活", "KTV", "夜店"],
    "culture": ["文化", "博物馆", "历史", "古迹", "寺庙", "遗址"],
    "nature": ["自然", "风景", "山", "湖", "公园", "户外"],
    "shopping": ["购物", "商场", "逛街", "买买买", "奢侈品"],
    "relax": ["休闲", "放松", "茶馆", "SPA", "温泉", "慢游"],
}
```

**偏好到工具调用的映射**:
```python
# 在engine.py中
# 每个偏好使用一个主关键词，避免API调用量爆炸
PREFERENCE_PRIMARY_KEYWORD = {
    "food": "美食餐厅",
    "entertainment": "娱乐场所",
    "culture": "博物馆景区",
    "nature": "公园风景区",
    "shopping": "购物中心",
    "relax": "休闲会所",
}

def _get_pois_by_preference(self, destination, preferences):
    """根据偏好获取POI
    
    API调用量控制：
    - 每个偏好只调用1次find_nearby
    - 使用主关键词而非多个keyword循环
    - 单偏好：1次调用
    - 双偏好：2次调用
    - 控制在API预算内
    """
    all_pois = []
    
    for pref in preferences:
        # 每个偏好只调用一次，使用主关键词
        keyword = PREFERENCE_PRIMARY_KEYWORD.get(pref)
        if not keyword:
            continue
        
        # 单次调用获取该偏好的POI
        result = self.amap_client.find_nearby(
            keyword=keyword,
            city=destination
        )
        if result.ok and result.raw:
            all_pois.extend(result.raw.get("pois", []))
    
    return all_pois
```

**API调用量分析**:
```
场景1: 无偏好
- 默认POI搜索: 1次
- 餐厅推荐(每天): days次
- 总计: 1 + days次 (2日游=3次, 5日游=6次)

场景2: 单偏好("吃吃吃")
- 偏好POI搜索: 1次
- 餐厅推荐(每天): days次
- 总计: 1 + days次 (2日游=3次, 5日游=6次)

场景3: 双偏好("美食+娱乐")
- 偏好POI搜索: 2次
- 餐厅推荐(每天): days次
- 总计: 2 + days次 (2日游=4次, 5日游=7次)

⚠️ 风险: 5日游接近8次上限
```

**API调用量保护**:
```python
# 在engine.py中添加天数上限保护
MAX_DINNER_RECOMMENDATION_DAYS = 3

for i, day_plan in enumerate(itinerary):
    # 只为前3天推荐餐厅，避免API调用量超限
    if i >= MAX_DINNER_RECOMMENDATION_DAYS:
        break
    
    last_stop = self._get_last_stop(day_plan)
    if last_stop:
        day_plan.dinner_recommendations = self._get_nearby_restaurants(last_stop)
```

**替代方案**（更优）:
```python
# 基于目的地city一次性搜索，复用到所有天
def _get_city_restaurants(self, destination):
    """一次性获取城市高分餐厅，复用到所有天"""
    result = self.amap_client.find_nearby(
        keyword="餐厅",
        city=destination
    )
    if result.ok and result.raw:
        pois = result.raw.get("pois", [])
        # 筛选高分餐厅
        return [p for p in pois if p.get("rating", 0) >= 4.0]
    return []

# 在plan()中
city_restaurants = self._get_city_restaurants(destination)
for day_plan in itinerary:
    # 从城市餐厅列表中随机选3家，避免重复
    day_plan.dinner_recommendations = random.sample(city_restaurants, min(3, len(city_restaurants)))
```

**推荐方案**: 使用替代方案，单次调用复用
- 2日游: 1次POI + 1次餐厅 = 2次
- 5日游: 1次POI + 1次餐厅 = 2次
- 双偏好5日游: 2次POI + 1次餐厅 = 3次
- 全部控制在8次上限内 ✅

**代码分支处理**:
```python
# 在engine.py的plan()方法中
if preferences:
    # 场景2: 有偏好，景点选择偏向偏好类型
    pois = self._get_pois_by_preference(destination, preferences)
else:
    # 场景1: 无偏好，正常获取综合景点
    pois = self._get_default_pois(destination)

# 两种场景都添加晚餐推荐
for day_plan in itinerary:
    last_stop = self._get_last_stop(day_plan)
    if last_stop:
        day_plan.dinner_recommendations = self._get_nearby_restaurants(last_stop)
```

**优先级**: P2（中等需求）

---

### 3. 智能时间分配

**需求**:
- 根据景点类型和用户偏好，智能分配游览时间
- 避免行程过于紧凑或松散

**实现方案**:
```python
# 景点时间估算
ATTRACTION_TIME_ESTIMATES = {
    "博物馆": 120,  # 分钟
    "公园": 90,
    "寺庙": 60,
    "商业街": 120,
    "自然景区": 180,
}

# 在clusterer.py中调整
def _assign_to_sessions(self, pois, travel_mode):
    for poi in pois:
        estimated_time = self._estimate_visit_time(poi)
        # 根据时间分配到上午/下午/晚上
```

**优先级**: P2（中等需求）

---

### 4. 多日游主题规划

**需求**:
- 3天以上行程，自动规划主题（如：第1天经典地标，第2天文化艺术，第3天自然风光）
- 避免行程单调重复

**实现方案**:
```python
# 在engine.py中
THEME_TEMPLATES = {
    1: ["经典地标游"],
    2: ["经典地标游", "文化艺术游"],
    3: ["经典地标游", "文化艺术游", "自然风光游"],
    4: ["经典地标游", "文化艺术游", "自然风光游", "休闲购物游"],
}

def _assign_themes(self, days):
    return THEME_TEMPLATES.get(days, ["综合游"] * days)
```

**优先级**: P3（低优先级，当前已有基础主题）

---

### 5. 实时路况和天气集成

**需求**:
- 集成实时路况，优化交通时间估算
- 集成天气预报，提醒用户注意事项

**实现方案**:
```python
# 在transit_estimator.py中
def estimate_transit_time(self, from_poi, to_poi, mode):
    # 调用高德实时路况API
    traffic_info = self.amap_client.get_traffic_info(...)
    
    # 根据路况调整时间
    base_time = self._calculate_base_time(...)
    adjusted_time = base_time * traffic_info.congestion_factor
    
    return adjusted_time
```

**优先级**: P3（需要额外API支持）

---

## M5实施计划

### 阶段1: 餐厅推荐（1-2天）

1. 在`engine.py`中添加餐厅查询逻辑
2. 更新`schema.py`支持`dinner_recommendations`字段
3. 调整LLM重写prompt包含餐厅推荐
4. 测试验证

### 阶段2: 用户偏好支持（2-3天）

1. 扩展`plan_trip()`参数
2. 更新`trip_router.py`识别偏好关键词
3. 调整景点筛选逻辑
4. 测试验证

### 阶段3: 其他增强（按需）

根据用户反馈和优先级，逐步实施其他功能。

---

## 验收标准

### M5.1 默认餐厅推荐（无偏好场景）

**场景**: 用户查询"帮我规划上海2日游"（无偏好关键词）

- ✅ 每天行程自动推荐3家高分餐厅
- ✅ 餐厅位于当天最后一个景点附近
- ✅ 景点选择为综合类型（地标、文化、自然等）
- ✅ LLM重写自然包含餐厅推荐
- ✅ 端到端测试通过率≥95%

**测试用例**:
```python
# 无偏好，应该推荐餐厅但景点为综合类型
("帮我规划上海2日游", {"destination": "上海", "days": 2, "preferences": None})
("北京3日游攻略", {"destination": "北京", "days": 3, "preferences": None})
```

### M5.2 美食偏好场景

**场景**: 用户查询"帮我规划一个吃吃吃的上海2日游"（有美食偏好）

- ✅ 景点本身偏向餐厅和小吃街
- ✅ 每天行程包含2-3个美食相关景点
- ✅ 晚上仍然推荐高分餐厅
- ✅ 意图路由准确识别"food"偏好
- ✅ 端到端测试通过率≥90%

**测试用例**:
```python
# 美食偏好，景点应该偏向餐厅和小吃街
("帮我规划一个吃吃吃的上海2日游", {"destination": "上海", "days": 2, "preferences": ["food"]})
("北京美食3日游", {"destination": "北京", "days": 3, "preferences": ["food"]})
```

### M5.3 其他偏好场景

**场景**: 用户查询"上海娱乐2日游"、"杭州文化3日游"等

- ✅ 支持5种偏好类型（美食/娱乐/文化/自然/购物/休闲）
- ✅ 意图路由准确识别偏好关键词
- ✅ 景点选择符合用户偏好
- ✅ 每种偏好有明确的keyword映射
- ✅ 端到端测试通过率≥90%

**测试用例**:
```python
("上海娱乐2日游", {"destination": "上海", "days": 2, "preferences": ["entertainment"]})
("杭州文化3日游", {"destination": "杭州", "days": 3, "preferences": ["culture"]})
("成都休闲2日游", {"destination": "成都", "days": 2, "preferences": ["relax"]})
```

---

## 当前状态

**M4状态**: 进行中
- ✅ 基础行程规划完成
- ✅ 地址信息已去除
- ✅ 输出长度已压缩（151-267字）
- ⏳ 生产环境集成待完成

**M5状态**: 待启动
- 等待M4完成后开始
- 优先实施餐厅推荐功能

---

**创建时间**: 2026-03-09  
**状态**: 规划中
