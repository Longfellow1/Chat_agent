#!/usr/bin/env python3
"""分析项目中的 Markdown 文档，识别重复和过程性内容"""

import os
import re
from pathlib import Path
from collections import defaultdict

def get_md_files():
    """获取所有 markdown 文件"""
    exclude_dirs = {'node_modules', '.venv', '.pytest_cache', '__pycache__'}
    md_files = []
    
    for root, dirs, files in os.walk('.'):
        # 过滤排除目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                md_files.append(filepath)
    
    return md_files

def analyze_file(filepath):
    """分析单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取关键信息
        lines = content.split('\n')
        title = lines[0].strip('#').strip() if lines else os.path.basename(filepath)
        
        # 统计
        word_count = len(content)
        line_count = len(lines)
        
        # 识别文档类型
        doc_type = classify_document(filepath, content, title)
        
        return {
            'path': filepath,
            'title': title,
            'type': doc_type,
            'size': word_count,
            'lines': line_count,
        }
    except Exception as e:
        return None

def classify_document(filepath, content, title):
    """分类文档类型"""
    path_lower = filepath.lower()
    content_lower = content.lower()
    title_lower = title.lower()
    
    # 里程碑完成报告
    if re.search(r'(m\d+.*completion|m\d+.*complete|m\d+.*report|m\d+.*summary)', path_lower):
        return 'milestone_completion'
    
    # 百度相关
    if 'baidu' in path_lower:
        return 'baidu_integration'
    
    # 测试报告
    if 'test' in path_lower and 'report' in path_lower:
        return 'test_report'
    
    # 项目状态
    if any(x in path_lower for x in ['status', 'progress', 'inventory', 'reconciliation']):
        return 'project_status'
    
    # 规范文档
    if 'spec/' in path_lower:
        return 'specification'
    
    # 文档指南
    if 'docs/' in path_lower:
        return 'documentation'
    
    # 问题追踪
    if any(x in title_lower for x in ['issue', 'help', 'problem', 'fix', 'debug']):
        return 'issue_tracking'
    
    # 验证任务
    if any(x in path_lower for x in ['verification', 'validation', 'remediation']):
        return 'verification'
    
    # 配置说明
    if any(x in title_lower for x in ['configuration', 'config', 'setup']):
        return 'configuration'
    
    return 'other'

def main():
    files = get_md_files()
    
    # 分析所有文件
    analyzed = []
    for f in files:
        result = analyze_file(f)
        if result:
            analyzed.append(result)
    
    # 按类型分组
    by_type = defaultdict(list)
    for item in analyzed:
        by_type[item['type']].append(item)
    
    # 输出统计
    print(f"总文档数: {len(analyzed)}\n")
    print("=" * 80)
    
    for doc_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n【{doc_type}】 ({len(items)} 个文件)")
        print("-" * 80)
        
        # 按大小排序
        items_sorted = sorted(items, key=lambda x: -x['size'])
        
        total_size = sum(item['size'] for item in items)
        print(f"总大小: {total_size:,} 字符\n")
        
        for item in items_sorted[:10]:  # 只显示前10个
            size_kb = item['size'] / 1024
            print(f"  {size_kb:6.1f}KB  {item['path']}")
        
        if len(items) > 10:
            print(f"  ... 还有 {len(items) - 10} 个文件")
    
    print("\n" + "=" * 80)
    print("\n建议删除的文档类型:")
    print("  - milestone_completion: 保留最终报告，删除中间过程文档")
    print("  - test_report: 保留最新的，删除旧的测试报告")
    print("  - issue_tracking: 已解决的问题可以删除")
    print("  - verification: 验证完成后可以删除")
    print("  - project_status: 合并为单一状态文档")

if __name__ == '__main__':
    main()
