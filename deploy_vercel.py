#!/usr/bin/env python3
import json
import hashlib
import time
import urllib.request
import urllib.error

TOKEN = 'vcp_3mspd9O3CPSBrt4jjTo9h3OXwOV6JT069jJNfvDXinPE04NwR73gb3LE'
TEAM_ID = 'team_C2l6j4UJ0x8Cwu7xvYtxBn02'

PROJECTS = [
    {'id': 'prj_ogrrPM7nncstax8qNgDhmtZ4IgLE', 'name': 'my-agy-ai-fleet'}, # Contains agy-aaa000.vercel.app
    {'id': 'prj_BWMgTGbwBc4KEQvyC1uvpL90DxCa', 'name': 'agy'}              # Contains agy-henna.vercel.app
]

FILES = [
    ('index.html', 'public/index.html'),
    ('vercel.json', 'vercel.json'),
    ('_headers', 'public/_headers'),
    ('_redirects', 'public/_redirects'),
]

def upload_file(file_name, local_path):
    with open(local_path, 'rb') as f:
        content = f.read()
    sha = hashlib.sha1(content).hexdigest()
    size = len(content)
    
    url = f'https://api.vercel.com/v2/files?teamId={TEAM_ID}'
    req = urllib.request.Request(
        url,
        data=content,
        headers={
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/octet-stream',
            'x-vercel-digest': sha,
            'Content-Length': str(size)
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            pass
    except urllib.error.HTTPError as e:
        if e.code != 409:
            print(f"Warning uploading {file_name}: {e}")
            
    return {'file': file_name, 'sha': sha, 'size': size}

def deploy_to_project(proj, uploaded_files):
    p_id = proj['id']
    p_name = proj['name']
    print(f"\n--- Deploying to {p_name} ({p_id}) ---")
    deploy_body = {
        'name': p_name,
        'project': p_id,
        'target': 'production',
        'files': uploaded_files
    }
    
    req_deploy = urllib.request.Request(
        f'https://api.vercel.com/v13/deployments?teamId={TEAM_ID}',
        data=json.dumps(deploy_body).encode('utf-8'),
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req_deploy) as resp:
        res = json.loads(resp.read().decode())
        uid = res['id']
        url = res.get('url')
        print(f"Deployment initiated: {uid} -> https://{url}")

    # Poll status
    print("Waiting for deployment to become READY...")
    for _ in range(30):
        time.sleep(2)
        req_status = urllib.request.Request(
            f'https://api.vercel.com/v13/deployments/{uid}?teamId={TEAM_ID}',
            headers={'Authorization': f'Bearer {TOKEN}'}
        )
        try:
            with urllib.request.urlopen(req_status) as resp:
                status_res = json.loads(resp.read().decode())
                state = status_res.get('readyState')
                print(f"  State: {state}")
                if state == 'READY':
                    print(f"✓ Deployment {p_name} READY!")
                    return True
                elif state == 'ERROR':
                    print(f"Deployment failed: {status_res.get('errorMessage')}")
                    return False
        except Exception as e:
            print(f"  Status check error: {e}")
            
    return False

def deploy():
    print("Uploading static assets to Vercel global store...")
    uploaded = []
    for fn, lp in FILES:
        info = upload_file(fn, lp)
        uploaded.append(info)
        print(f"  ✓ {fn} ({info['size']} bytes, sha1: {info['sha'][:8]})")
        
    for proj in PROJECTS:
        deploy_to_project(proj, uploaded)

    # Verify primary alias
    test_urls = [
        "https://agy-aaa000.vercel.app/?v=4.6",
        "https://my-agy-ai-fleet.vercel.app/?v=4.6",
        "https://agy-henna.vercel.app/?v=4.6"
    ]
    for test_url in test_urls:
        print(f"\nVerifying live alias {test_url}...")
        try:
            req_verify = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_verify, timeout=10) as resp:
                body = resp.read().decode('utf-8')
                if "Executive Admin Dashboard" in body:
                    print(f"✓ SUCCESS: 'Executive Admin Dashboard' is active on {test_url}!")
                else:
                    print(f"! Warning: 'Executive Admin Dashboard' not found yet on {test_url}.")
        except Exception as e:
            print(f"Verification error for {test_url}: {e}")

if __name__ == '__main__':
    deploy()
