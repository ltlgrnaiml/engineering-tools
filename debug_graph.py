"""Debug script to analyze graph data."""
import requests

r = requests.get('http://localhost:8000/api/devtools/artifacts/graph')
data = r.json()
nodes = data['nodes']
edges = data['edges']

# Get all node IDs
node_ids = {n['id'] for n in nodes}

# Check DISC nodes
disc_nodes = [n for n in nodes if n['id'].startswith('DISC-')]
print('DISC node IDs:', [n['id'] for n in disc_nodes])

# Check edges with DISC
disc_edges = [e for e in edges if 'DISC-' in e['target'] or 'DISC-' in e['source']]
print(f'\nEdges involving DISC: {len(disc_edges)}')

# Check if all edge endpoints exist as nodes
missing_sources = []
missing_targets = []
for e in edges:
    if e['source'] not in node_ids:
        missing_sources.append(e['source'])
    if e['target'] not in node_ids:
        missing_targets.append(e['target'])

print(f'\nMissing source nodes: {set(missing_sources)}')
print(f'Missing target nodes: {set(missing_targets)}')

# Print first 5 edges
print('\nFirst 5 edges:')
for e in edges[:5]:
    src_exists = e['source'] in node_ids
    tgt_exists = e['target'] in node_ids
    print(f"  {e['source']} -> {e['target']} (src exists: {src_exists}, tgt exists: {tgt_exists})")
