# Verify RPC endpoints are CORS-friendly for browser fetch
import urllib.request
import json

endpoints = [
    ("TON Toncenter", "https://toncenter.com/api/v2/getAddressInformation?address=UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"),
    ("Bitcoin Mempool", "https://mempool.space/api/address/bc1peg8n6rv7lnzpdwgqqktcyxvrw7we60c780l2yh48pvqvgpj2p7gsvecjdg"),
]

for name, url in endpoints:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            headers = dict(r.getheaders())
            cors = headers.get("access-control-allow-origin", "none")
            print(f"{name}: HTTP {r.status}, CORS header: {cors}")
    except Exception as e:
        print(f"{name} error: {e}")
