import re

q_clean = '我在天津天河哪里有加油站'
near_pattern = r'(?<!我)(?<!在)(?<!去)(?<!到)([\u4e00-\u9fa5A-Za-z0-9]{2,20})(附近|周边|旁边|周围|一带|哪里)'
match = re.search(near_pattern, q_clean)
if match:
    print(f'Matched: {match.group(0)}')
    print(f'Group 1: {match.group(1)}')
else:
    print('No match')
