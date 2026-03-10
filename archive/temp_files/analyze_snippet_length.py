#!/usr/bin/env python3
"""分析实际 snippet 长度"""
import sys
import os
sys.path.insert(0, 'agent_service')

os.environ['APPBUILDER_TOKEN'] = 'REDACTED'

import appbuilder

search = appbuilder.AISearch()
result = search.run(messages=[{'role': 'user', 'content': '特斯拉Model 3最新价格'}])

print('实际 snippet 长度分析:')
print('='*80)

lengths = []
for i, ref in enumerate(result.content.references[:10], 1):
    content = ref.content or ''
    lengths.append(len(content))
    print(f'\n{i}. 标题: {ref.title[:50]}...')
    print(f'   长度: {len(content)} 字符')
    print(f'   前150字: {content[:150]}')
    if len(content) > 80:
        print(f'   80字截断: {content[:80]}')
        print(f'   200字截断: {content[:200]}')

print(f'\n{'='*80}')
print(f'统计:')
print(f'  平均长度: {sum(lengths)/len(lengths):.0f} 字符')
print(f'  最短: {min(lengths)} 字符')
print(f'  最长: {max(lengths)} 字符')
print(f'  中位数: {sorted(lengths)[len(lengths)//2]} 字符')
