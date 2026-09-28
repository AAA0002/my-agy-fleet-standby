#!/usr/bin/env python3
import json
import hashlib
import time
import urllib.request
import urllib.error

TOKEN = 'vcp_3mspd9O3CPSBrt4jjTo9h3OXwOV6JT069jJNfvDXinPE04NwR73gb3LE'
TEAM_ID = 'team_C2l6j4UJ0x8Cwu7xvYtxBn02'

ADMIN_PROJECT = {'id': 'prj_ogrrPM7nncstax8qNgDhmtZ4IgLE', 'name': 'my-agy-ai-fleet'} # agy-aaa000.vercel.app
ADMIN_PROJECT_2 = {'id': 'prj_cRQOVIEldwoVTdZy45GQ95hcGhy1', 'name': 'aaa-free-ai'}       # aaa-free-ai.vercel.app
ADS_PROJECT   = {'id': 'prj_BWMgTGbwBc4KEQvyC1uvpL90DxCa', 'name': 'agy'}              # agy-henna.vercel.app

ADMIN_FILES = [
    ('index.html', 'public_admin/index.html'),
    ('user-admin.html', 'public_admin/user-admin.html'),
    ('users.html', 'public_admin/user-admin.html'),
    ('admin.html', 'public_admin/admin.html'),
    ('vercel.json', 'public_admin/vercel.json'),
    ('_headers', 'public_admin/_headers'),
    ('_redirects', 'public_admin/_redirects'),
]

ADS_FILES = [
    ('index.html', 'public_ads/index.html'),
    ('app/ad/index.html', 'public_ads/app/ad/index.html'),
    ('shared/waterfallController.js', 'public_ads/shared/waterfallController.js'),
    ('shared/gigapubController.js', 'public_ads/shared/gigapubController.js'),
    ('shared/vastLoader.js', 'public_ads/shared/vastLoader.js'),
    ('shared/audio.js', 'public_ads/shared/audio.js'),
    ('shared/geo.js', 'public_ads/shared/geo.js'),
    ('shared/i18n.js', 'public_ads/shared/i18n.js'),
    ('vercel.json', 'public_ads/vercel.json'),
    ('_headers', 'public_ads/_headers'),
    ('_redirects', 'public_ads/_redirects'),
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
    print("=== DEPLOYING DEDICATED ADMIN DASHBOARD TO VERCEL (my-agy-ai-fleet) ===")
    admin_uploaded = []
    for fn, lp in ADMIN_FILES:
        info = upload_file(fn, lp)
        admin_uploaded.append(info)
        print(f"  ✓ {fn} ({info['size']} bytes)")
    deploy_to_project(ADMIN_PROJECT, admin_uploaded)

    print("\n=== DEPLOYING DEDICATED ADMIN DASHBOARD TO VERCEL (aaa-free-ai) ===")
    deploy_to_project(ADMIN_PROJECT_2, admin_uploaded)

    print("\n=== DEPLOYING DEDICATED WATCH ADS PORTAL TO VERCEL (agy) ===")
    ads_uploaded = []
    for fn, lp in ADS_FILES:
        info = upload_file(fn, lp)
        ads_uploaded.append(info)
        print(f"  ✓ {fn} ({info['size']} bytes)")
    deploy_to_project(ADS_PROJECT, ads_uploaded)

    # Verification
    print("\n--- Verifying Vercel Deployments ---")
    try:
        req = urllib.request.Request("https://agy-aaa000.vercel.app/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode('utf-8')
            if "User Bot Admin Console" in body or "ADMIN SECURITY GATE" in body:
                print("✓ SUCCESS: Admin Console active on https://agy-aaa000.vercel.app/ (ZERO ADS)")
            else:
                print("! Notice: Body on agy-aaa000:", body[:100])
    except Exception as e:
        print("Admin verify err (agy-aaa000):", e)

    try:
        req = urllib.request.Request("https://aaa-free-ai.vercel.app/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode('utf-8')
            if "User Bot Admin Console" in body or "ADMIN SECURITY GATE" in body:
                print("✓ SUCCESS: Admin Console active on https://aaa-free-ai.vercel.app/ (ZERO ADS)")
            else:
                print("! Notice: Body on aaa-free-ai:", body[:100])
    except Exception as e:
        print("Admin verify err (aaa-free-ai):", e)

    try:
        req = urllib.request.Request("https://agy-henna.vercel.app/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode('utf-8')
            if "Watch Sponsored Ad" in body:
                print("✓ SUCCESS: Watch Ads Portal active on https://agy-henna.vercel.app/ (ZERO ADMIN)")
            else:
                print("! Notice: Body on agy-henna:", body[:100])
    except Exception as e:
        print("Ads verify err:", e)

if __name__ == '__main__':
    deploy()
