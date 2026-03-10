"""100条Location Intent测试用例

测试分类：
- 80条正例：标准的周边推荐查询
- 10条难例：复杂的多约束查询
- 10条负例：不应该触发location intent的查询
"""

import pytest
from domain.location.parser import parse_location_intent
from domain.location.amap_type_codes import get_amap_type_code, is_supported_by_amap


# ========== 80条正例 ==========
POSITIVE_CASES = [
    # 餐饮类 (30条)
    ("上海静安寺附近的咖啡厅", "上海", "静安寺", "咖啡厅", "050500"),
    ("北京国贸周边的西餐厅", "北京", "国贸", "西餐厅", "050200"),
    ("杭州西湖旁边的火锅店", "杭州", "西湖", "火锅", "050117"),
    ("深圳华强北的川菜馆", "深圳", "华强北", "川菜", "050101"),
    ("广州珠江新城的粤菜", "广州", "珠江新城", "粤菜", "050102"),
    ("成都春熙路的烧烤店", "成都", "春熙路", "烧烤", "050118"),
    ("南京新街口的日料", "南京", "新街口", "日料", "050201"),
    ("武汉光谷的韩餐", "武汉", "光谷", "韩餐", "050202"),
    ("西安钟楼附近的湘菜", "西安", "钟楼", "湘菜", "050104"),
    ("重庆解放碑的火锅", "重庆", "解放碑", "火锅", "050117"),
    ("苏州观前街的海鲜", "苏州", "观前街", "海鲜", "050119"),
    ("天津滨江道的快餐", "天津", "滨江道", "快餐", "050300"),
    ("青岛五四广场的烤肉", "青岛", "五四广场", "烤肉", "050118"),
    ("厦门中山路的甜品店", "厦门", "中山路", "甜品", "050402"),
    ("长沙五一广场的茶馆", "长沙", "五一广场", "茶馆", "050600"),
    ("郑州二七广场的奶茶店", "郑州", "二七广场", "奶茶", "050700"),
    ("济南泉城广场的面包店", "济南", "泉城广场", "面包店", "050401"),
    ("福州三坊七巷的素食", "福州", "三坊七巷", "素食", "050109"),
    ("昆明翠湖的云贵菜", "昆明", "翠湖", "云贵菜", "050108"),
    ("大连星海广场的东北菜", "大连", "星海广场", "东北菜", "050106"),
    ("上海人民广场的肯德基", "上海", "人民广场", "肯德基", "050301"),
    ("北京西单的麦当劳", "北京", "西单", "麦当劳", "050302"),
    ("深圳罗湖的茶餐厅", "深圳", "罗湖", "茶餐厅", "050305"),
    ("广州天河城的法餐", "广州", "天河城", "法餐", "050204"),
    ("杭州武林广场的泰餐", "杭州", "武林广场", "泰餐", "050206"),
    ("南京夫子庙的牛排", "南京", "夫子庙", "牛排", "050211"),
    ("成都太古里的意大利餐", "成都", "太古里", "意大利菜", "050205"),
    ("武汉江汉路的印度餐", "武汉", "江汉路", "印度菜", "050204"),
    ("西安大雁塔的清真菜", "西安", "大雁塔", "清真", "050121"),
    ("重庆观音桥的老字号", "重庆", "观音桥", "老字号", "050116"),
    
    # 购物类 (15条)
    ("上海南京路的商场", "上海", "南京路", "商场", "060100"),
    ("北京王府井的购物中心", "北京", "王府井", "购物中心", "060101"),
    ("深圳东门的便利店", "深圳", "东门", "便利店", "060200"),
    ("广州北京路的超市", "广州", "北京路", "超市", "060300"),
    ("杭州湖滨的书店", "杭州", "湖滨", "书店", "061205"),
    ("南京新街口的眼镜店", "南京", "新街口", "眼镜店", "061204"),
    ("成都春熙路的服装店", "成都", "春熙路", "服装店", "061101"),
    ("武汉江汉路的鞋店", "武汉", "江汉路", "鞋店", "061102"),
    ("西安小寨的数码店", "西安", "小寨", "数码", "060306"),
    ("重庆解放碑的珠宝店", "重庆", "解放碑", "珠宝", "061202"),
    ("苏州观前街的礼品店", "苏州", "观前街", "礼品店", "061209"),
    ("天津和平路的烟酒店", "天津", "和平路", "烟酒", "061210"),
    ("青岛台东的体育用品", "青岛", "台东", "体育用品", "060900"),
    ("厦门中山路的免税店", "厦门", "中山路", "免税店", "060103"),
    ("长沙黄兴路的步行街", "长沙", "黄兴路", "步行街", "061001"),
    
    # 生活服务类 (10条)
    ("上海徐家汇的理发店", "上海", "徐家汇", "理发", "071100"),
    ("北京三里屯的美容院", "北京", "三里屯", "美容", "071100"),
    ("深圳福田的洗衣店", "深圳", "福田", "洗衣", "071500"),
    ("广州天河的快递", "广州", "天河", "快递", "070500"),
    ("杭州西湖的照相馆", "杭州", "西湖", "照相", "071600"),
    ("南京新街口的按摩店", "南京", "新街口", "按摩", "071200"),
    ("成都春熙路的足疗", "成都", "春熙路", "足疗", "071200"),
    ("武汉光谷的驾校", "武汉", "光谷", "驾校", "141500"),
    ("西安钟楼的律师事务所", "西安", "钟楼", "律师", "070701"),
    ("重庆解放碑的彩票店", "重庆", "解放碑", "彩票", "071800"),
    
    # 体育休闲类 (10条)
    ("上海静安寺的健身房", "上海", "静安寺", "健身", "080111"),
    ("北京朝阳的游泳馆", "北京", "朝阳", "游泳", "080110"),
    ("深圳南山的电影院", "深圳", "南山", "电影院", "080601"),
    ("广州天河的KTV", "广州", "天河", "KTV", "080302"),
    ("杭州西湖的酒吧", "杭州", "西湖", "酒吧", "080304"),
    ("南京新街口的网吧", "南京", "新街口", "网吧", "080308"),
    ("成都春熙路的桌游吧", "成都", "春熙路", "桌游", "080309"),
    ("武汉光谷的保龄球馆", "武汉", "光谷", "保龄球", "080102"),
    ("西安钟楼的音乐厅", "西安", "钟楼", "音乐厅", "080602"),
    ("重庆解放碑的游乐场", "重庆", "解放碑", "游乐场", "080501"),
    
    # 医疗类 (5条)
    ("上海徐家汇的医院", "上海", "徐家汇", "医院", "090100"),
    ("北京海淀的药店", "北京", "海淀", "药店", "090601"),
    ("深圳福田的诊所", "深圳", "福田", "诊所", "090300"),
    ("广州天河的口腔医院", "广州", "天河", "口腔", "090202"),
    ("杭州西湖的宠物医院", "杭州", "西湖", "宠物医院", "090701"),
    
    # 住宿类 (5条)
    ("上海外滩的酒店", "上海", "外滩", "酒店", "100100"),
    ("北京故宫附近的宾馆", "北京", "故宫", "宾馆", "100100"),
    ("深圳世界之窗的快捷酒店", "深圳", "世界之窗", "快捷酒店", "100102"),
    ("广州白云山的民宿", "广州", "白云山", "民宿", "100200"),
    ("杭州西湖的青年旅舍", "杭州", "西湖", "青年旅舍", "100201"),
    
    # 交通类 (5条)
    ("上海虹桥的停车场", "上海", "虹桥", "停车场", "150700"),
    ("北京西站的加油站", "北京", "西站", "加油站", "150800"),
    ("深圳机场的充电站", "深圳", "机场", "充电站", "150900"),
    ("广州南站的地铁站", "广州", "南站", "地铁", "150500"),
    ("杭州东站的公交站", "杭州", "东站", "公交", "150702"),
]


# ========== 10条难例 ==========
HARD_CASES = [
    # 多约束条件
    ("上海静安寺周边人均100元的西餐厅", "上海", "静安寺", "西餐厅", "050200"),
    ("北京国贸附近24小时营业的便利店", "北京", "国贸", "便利店", "060200"),
    ("深圳华强北有停车位的商场", "深圳", "华强北", "商场", "060100"),
    ("广州天河城最近的星巴克", "广州", "天河城", "咖啡厅", "050500"),
    ("杭州西湖评分最高的餐厅", "杭州", "西湖", "餐厅", "050000"),
    
    # 复杂地点描述
    ("上海市浦东新区陆家嘴金融中心附近的咖啡厅", "上海", "陆家嘴", "咖啡厅", "050500"),
    ("北京市朝阳区三里屯太古里南区的酒吧", "北京", "三里屯", "酒吧", "080304"),
    ("深圳市南山区科技园地铁站出口的快餐店", "深圳", "科技园", "快餐", "050300"),
    
    # 隐含需求
    ("上海静安寺附近能让脖子放松的地方", "上海", "静安寺", "", ""),  # 需要推断为按摩店
    ("北京国贸周边适合商务会谈的场所", "北京", "国贸", "", ""),  # 需要推断为咖啡厅或餐厅
]


# ========== 10条负例 ==========
NEGATIVE_CASES = [
    # 非地点查询
    "今天天气怎么样",
    "明天会下雨吗",
    "帮我订一张机票",
    "查询快递单号",
    "设置一个闹钟",
    
    # 不支持的POI类型
    "上海静安寺附近的密室逃脱",
    "北京国贸周边的剧本杀",
    "深圳华强北的VR体验馆",
    "广州天河城的电竞馆",
    "杭州西湖的轰趴馆",
]


def test_positive_cases():
    """测试80条正例"""
    passed = 0
    failed = []
    
    for query, expected_city, expected_anchor, expected_category, expected_type_code in POSITIVE_CASES:
        intent = parse_location_intent(query)
        type_code = get_amap_type_code(intent.category) if intent.category else ""
        
        # 验证解析结果（放宽category匹配条件）
        city_match = expected_city in intent.city if intent.city else False
        anchor_match = expected_anchor in intent.anchor_poi if intent.anchor_poi else False
        # Category可以是expected_category或其变体（如"火锅"或"火锅店"）
        category_match = (
            intent.category == expected_category or
            expected_category in intent.category or
            intent.category in expected_category
        )
        type_code_match = type_code == expected_type_code
        
        if city_match and anchor_match and category_match and type_code_match:
            passed += 1
        else:
            failed.append({
                "query": query,
                "expected": {
                    "city": expected_city,
                    "anchor": expected_anchor,
                    "category": expected_category,
                    "type_code": expected_type_code
                },
                "actual": {
                    "city": intent.city,
                    "anchor": intent.anchor_poi,
                    "category": intent.category,
                    "type_code": type_code
                }
            })
    
    print(f"\n正例测试结果: {passed}/{len(POSITIVE_CASES)} 通过")
    if failed:
        print(f"\n失败案例 ({len(failed)}条):")
        for item in failed[:10]:  # 只显示前10条
            print(f"  Query: {item['query']}")
            print(f"    Expected: {item['expected']}")
            print(f"    Actual: {item['actual']}")
    
    assert passed >= 60, f"正例通过率过低: {passed}/{len(POSITIVE_CASES)}"


def test_hard_cases():
    """测试10条难例"""
    passed = 0
    failed = []
    
    for query, expected_city, expected_anchor, expected_category, expected_type_code in HARD_CASES:
        intent = parse_location_intent(query)
        
        # 难例只要求提取出城市和锚点即可
        city_match = expected_city in intent.city if intent.city else False
        anchor_match = expected_anchor in intent.anchor_poi if intent.anchor_poi else False
        
        if city_match and anchor_match:
            passed += 1
        else:
            failed.append({
                "query": query,
                "expected": {"city": expected_city, "anchor": expected_anchor},
                "actual": {"city": intent.city, "anchor": intent.anchor_poi}
            })
    
    print(f"\n难例测试结果: {passed}/{len(HARD_CASES)} 通过")
    if failed:
        print(f"\n失败案例:")
        for item in failed:
            print(f"  Query: {item['query']}")
            print(f"    Expected: {item['expected']}")
            print(f"    Actual: {item['actual']}")
    
    assert passed >= 5, f"难例通过率过低: {passed}/{len(HARD_CASES)}"


def test_negative_cases():
    """测试10条负例"""
    passed = 0
    failed = []
    
    for query in NEGATIVE_CASES:
        intent = parse_location_intent(query)
        
        # 负例应该confidence很低或者category不支持
        is_negative = (
            intent.confidence < 0.3 or
            (intent.category and not is_supported_by_amap(intent.category))
        )
        
        if is_negative:
            passed += 1
        else:
            failed.append({
                "query": query,
                "intent": {
                    "city": intent.city,
                    "anchor": intent.anchor_poi,
                    "category": intent.category,
                    "confidence": intent.confidence
                }
            })
    
    print(f"\n负例测试结果: {passed}/{len(NEGATIVE_CASES)} 通过")
    if failed:
        print(f"\n失败案例:")
        for item in failed:
            print(f"  Query: {item['query']}")
            print(f"    Intent: {item['intent']}")
    
    assert passed >= 8, f"负例通过率过低: {passed}/{len(NEGATIVE_CASES)}"


def test_type_code_coverage():
    """测试POI类型码覆盖率"""
    categories = set()
    for query, _, _, category, _ in POSITIVE_CASES:
        if category:
            categories.add(category)
    
    supported = sum(1 for cat in categories if is_supported_by_amap(cat))
    coverage = supported / len(categories) * 100
    
    print(f"\nPOI类型码覆盖率: {supported}/{len(categories)} ({coverage:.1f}%)")
    
    unsupported = [cat for cat in categories if not is_supported_by_amap(cat)]
    if unsupported:
        print(f"不支持的类别: {unsupported}")
    
    assert coverage >= 95, f"POI类型码覆盖率过低: {coverage:.1f}%"


if __name__ == "__main__":
    print("=" * 80)
    print("Location Intent 100条测试用例")
    print("=" * 80)
    
    test_positive_cases()
    test_hard_cases()
    test_negative_cases()
    test_type_code_coverage()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
