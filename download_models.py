import os
import requests

def download_file(url, path):
    print(f"Downloading {url}...")
    r = requests.get(url)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            f.write(r.content)
        print(f"Saved to {path}")
    else:
        print(f"Failed to download {url}")

def main():
    os.makedirs('static/models', exist_ok=True)
    
    base_url = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/'
    models = [
        'tiny_face_detector_model-weights_manifest.json',
        'tiny_face_detector_model-shard1',
        'face_expression_model-weights_manifest.json',
        'face_expression_model-shard1'
    ]
    
    for m in models:
        download_file(base_url + m, os.path.join('static', 'models', m))

if __name__ == '__main__':
    main()
