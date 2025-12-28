import json
import os
import random
from datetime import datetime

# Function to generate synthetic data for one process (post_litho or post_etch)
def generate_data(process):
    means = {'post_litho': {'cd': 180, 'lwr': 5}, 'post_etch': {'cd': 130, 'lwr': 4}}
    sigmas = {'post_litho': {'cd': 3, 'lwr': 0.5}, 'post_etch': {'cd': 2, 'lwr': 0.4}}
    mean_cd = means[process]['cd']
    sigma_cd = sigmas[process]['cd']
    mean_lwr = means[process]['lwr']
    sigma_lwr = sigmas[process]['lwr']
    
    data = {}
    for w in range(1, 4):  # 3 wafers
        wafer_id = f'W{w:02d}'
        data[wafer_id] = {}
        for s in range(1, 21):  # 20 sites
            site_id = f'S{s:02d}'
            features = []
            for f in range(1, 6):  # 5 features
                feature = {
                    'feature_id': f'F{f:02d}',
                    'type': 'line_space',
                    'pitch_nm': 250,
                    'cd_nm': round(random.normalvariate(mean_cd, sigma_cd), 2),
                    'lwr_nm': round(random.normalvariate(mean_lwr, sigma_lwr), 2)
                }
                features.append(feature)
            data[wafer_id][site_id] = features
    return data

# Generate base template
base_data = {
    'meta': {
        'lot_id': 'LOT001',
        'recipe_name': 'Standard_Litho_Etch',
        'cd_sem': 'Hitachi_CDSEM',
        'created_at': datetime.now().isoformat()
    },
    'images': []  # Placeholder; can add fake image names per feature if needed
}

# Create directory and generate files
os.makedirs('fake_repo', exist_ok=True)
num_files = 1000  # Scale to thousands as needed
for i in range(num_files):
    file_data = base_data.copy()
    file_data['meta']['lot_id'] = f'LOT{i:04d}'
    process = random.choice(['post_litho', 'post_etch'])
    file_data[process] = generate_data(process)
    filename = f'fake_repo/sem_data_{process}_{i:04d}.json'  # Filename aids regex extraction
    with open(filename, 'w') as f:
        json.dump(file_data, f, indent=2)

print(f'Generated {num_files} JSON files in fake_repo directory.')