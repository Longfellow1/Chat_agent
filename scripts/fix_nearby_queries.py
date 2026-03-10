#!/usr/bin/env python3
"""修复评测数据中"附近/周边"查询缺少城市实体的问题

真实链路中，这些查询会被补充城市信息，评测数据也应该反映这一点。
"""

import csv
import re
from pathlib import Path

# 城市+街道/地标 组合池（包含常见、模糊、生僻地点，考察鲁棒性）
LOCATION_PAIRS = [
    # 常见地标
    ("北京", "三里屯"),
    ("北京", "国贸"),
    ("上海", "南京路"),
    ("上海", "陆家嘴"),
    ("广州", "珠江新城"),
    ("广州", "天河路"),
    ("深圳", "华强北"),
    ("深圳", "科技园"),
    
    # 模糊地点（需要推理）
    ("杭州", "西湖边"),
    ("杭州", "武林广场"),
    ("成都", "春熙路"),
    ("成都", "宽窄巷子"),
    ("重庆", "解放碑"),
    ("重庆", "观音桥"),
    ("西安", "钟楼"),
    ("西安", "大雁塔"),
    
    # 生僻地点（考察容错）
    ("南京", "新街口"),
    ("南京", "夫子庙"),
    ("武汉", "光谷"),
    ("武汉", "江汉路"),
    ("苏州", "观前街"),
    ("苏州", "金鸡湖"),
    ("天津", "滨江道"),
    ("天津", "意式风情街"),
    
    # 更多挑战性地点
    ("长沙", "五一广场"),
    ("长沙", "橘子洲"),
    ("郑州", "二七广场"),
    ("郑州", "花园路"),
    ("青岛", "五四广场"),
    ("青岛", "台东"),
]

def fix_nearby_query(query: str, location_index: int) -> str:
    """修复附近/周边查询，添加城市+街道/地标实体
    
    规则：
    1. "附近" -> "在{城市}{街道/地标}附近"
    2. "周边" -> "在{城市}{街道/地标}周边"  
    3. "这附近" -> "在{城市}{街道/地标}这附近"
    4. 如果已有城市名（如"上海外滩周边"），保持不变
    
    包含常见、模糊、生僻地点，考察nearby鲁棒性
    
    Args:
        query: 原始查询
        location_index: 位置索引（用于循环分配城市+街道/地标）
        
    Returns:
        修复后的查询
    """
    # 检查是否已包含城市名
    for city, _ in LOCATION_PAIRS:
        if city in query:
            return query  # 已有城市，不修改
    
    # 选择城市+街道/地标（循环分配）
    city, landmark = LOCATION_PAIRS[location_index % len(LOCATION_PAIRS)]
    location = f"{city}{landmark}"
    
    # 修复模式
    patterns = [
        (r'^(.*?)这附近', rf'\1在{location}这附近'),
        (r'^(.*?)附近', rf'\1在{location}附近'),
        (r'^(.*?)周边', rf'\1在{location}周边'),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, query):
            return re.sub(pattern, replacement, query)
    
    return query


def main():
    input_file = Path("archive/csv_data/testset_200条_0309.csv")
    output_file = Path("archive/csv_data/testset_200条_0309_fixed.csv")
    
    if not input_file.exists():
        print(f"错误：找不到文件 {input_file}")
        return
    
    fixed_count = 0
    location_index = 0
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        for row in reader:
            if not row:
                writer.writerow(row)
                continue
            
            # CSV格式：id, query, rewritten_query, ...
            if len(row) < 2:
                writer.writerow(row)
                continue
            
            original_query = row[1]
            
            # 检查是否包含"附近"或"周边"
            if "附近" in original_query or "周边" in original_query:
                fixed_query = fix_nearby_query(original_query, location_index)
                
                if fixed_query != original_query:
                    print(f"修复: {original_query} -> {fixed_query}")
                    row[1] = fixed_query
                    # 如果有rewritten_query字段，也同步修改
                    if len(row) > 2 and row[2]:
                        row[2] = fixed_query
                    fixed_count += 1
                    location_index += 1
            
            writer.writerow(row)
    
    print(f"\n完成！共修复 {fixed_count} 条数据")
    print(f"输出文件：{output_file}")
    
    # 显示修复示例
    print("\n修复示例：")
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        count = 0
        for row in reader:
            if len(row) > 1 and ("附近" in row[1] or "周边" in row[1]):
                print(f"  {row[0]}: {row[1]}")
                count += 1
                if count >= 5:
                    break


if __name__ == "__main__":
    main()
