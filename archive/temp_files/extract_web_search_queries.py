import csv
import random

# Read CSV and filter web search queries
web_search_queries = []

with open('testset_eval_1000_v3.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        tool = row.get('tool', '').strip()
        query = row.get('query', '').strip()
        
        # Filter for web_search tool
        if tool == 'web_search' and query:
            web_search_queries.append({
                'query': query,
                'tool': tool,
                'expected': row.get('expected_output', '').strip()
            })

print(f"Total web_search queries: {len(web_search_queries)}")

# Sample 30 queries
if len(web_search_queries) > 30:
    sampled = random.sample(web_search_queries, 30)
else:
    sampled = web_search_queries

# Save to file
with open('web_search_30_queries.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['query', 'tool', 'expected'])
    writer.writeheader()
    writer.writerows(sampled)

print(f"Sampled {len(sampled)} queries")
print("\nFirst 5 queries:")
for i, q in enumerate(sampled[:5], 1):
    print(f"{i}. {q['query']}")
