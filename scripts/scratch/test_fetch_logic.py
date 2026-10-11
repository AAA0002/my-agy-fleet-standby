import urllib.request
import json

addr = 'UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT'
url = f'https://toncenter.com/api/v2/getAddressInformation?address={addr}'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read().decode())
    nanotons = int(data['result']['balance'])
    print("Derived Live TON on-chain balance:", nanotons / 1e9, "TON")
