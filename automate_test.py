import requests
import time
import os
import sys

BASE_URL = "http://localhost:8000"
PDF_PATH = "/Users/lizhouyuan/E盘/MDX製作/测试/最新/最新/中古近代汉语探微_董志翹.pdf"
INDEX_PATH = "/Users/lizhouyuan/E盘/MDX製作/测试/最新/最新/《中古近代汉语探微》董志翘，中华书局2007-目录与词汇索引.xlsx"

def wait_for_task(task_id, type_name):
    print(f"Waiting for {type_name} task {task_id}...")
    while True:
        resp = requests.get(f"{BASE_URL}/api/status/{task_id}")
        data = resp.json()
        state = data.get('state')
        if state == 'SUCCESS':
            print(f"{type_name} complete!")
            return data.get('result')
        elif state == 'FAILURE':
            print(f"{type_name} failed: {data.get('status')}")
            sys.exit(1)
        elif state == 'PROGRESS':
            print(f"Progress: {data.get('current')}/{data.get('total')} - {data.get('status')}")
        else:
            print(f"State: {state}")
        time.sleep(2)

def run_test():
    # 1. Upload PDF
    print("Uploading PDF...")
    with open(PDF_PATH, 'rb') as f:
        resp = requests.post(f"{BASE_URL}/api/upload", files={'file': f})
    
    data = resp.json()
    if 'error' in data:
        print(f"Upload failed: {data['error']}")
        sys.exit(1)
    
    task_id = data['task_id']
    print(f"Upload success! Task ID: {task_id}")

    # 2. Start Conversion
    print("Starting conversion...")
    resp = requests.post(f"{BASE_URL}/api/convert", json={
        'task_id': task_id,
        'dpi': 200,
        'quality': 85,
        'crop': False
    })
    celery_task_id = resp.json()['celery_task_id']
    wait_for_task(celery_task_id, "Conversion")

    # 3. Upload Index
    print("Uploading index...")
    with open(INDEX_PATH, 'rb') as f:
        resp = requests.post(f"{BASE_URL}/api/upload-index", 
                             data={'task_id': task_id, 'body_start': 1},
                             files={'file': f})
    
    celery_task_id = resp.json()['celery_task_id']
    index_result = wait_for_task(celery_task_id, "Index Processing")
    print(f"Processed {index_result.get('count')} index items.")

    # 4. Build MDX
    print("Building MDX...")
    config = """[global]
templ_choice = "B"
name = "中古近代汉语探微"
name_abbr = "ZGJDHYTW"
simp_trad_flg = false

[template]
[template.b]
body_start = 1
"""
    resp = requests.post(f"{BASE_URL}/api/build", json={
        'task_id': task_id,
        'config': config
    })
    celery_task_id = resp.json()['celery_task_id']
    build_result = wait_for_task(celery_task_id, "Build")
    print(f"MDX files generated: {build_result.get('files')}")

    # 5. Download check (just headers)
    print("Checking download...")
    resp = requests.get(f"{BASE_URL}/api/download/{task_id}", stream=True)
    if resp.status_code == 200:
        print("Final result is ready for download!")
    else:
        print(f"Download check failed: {resp.status_code}")

if __name__ == "__main__":
    run_test()
