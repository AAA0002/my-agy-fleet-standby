#!/usr/bin/env python3
"""
DigitalPlat DNS Manager
Authoritative DNS manager for DigitalPlat FreeDomain domains (agy.dpdns.org).
Operates directly against the official DigitalPlat API.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load root environment
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

API_BASE = "https://domain-api.digitalplat.org/api/v1"
API_KEY = os.getenv("DIGITALPLAT_API_KEY")

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="126", "Google Chrome";v="126", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def get_headers():
    if not API_KEY:
        raise ValueError("Missing DIGITALPLAT_API_KEY in .env")
    h = BROWSER_HEADERS.copy()
    h["Authorization"] = f"Bearer {API_KEY}"
    return h

def list_domains():
    r = requests.get(f"{API_BASE}/domains", headers=get_headers(), timeout=10)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
        return []
    return r.json().get("data", [])

def get_domain_records(domain="agy.dpdns.org"):
    r = requests.get(f"{API_BASE}/domains/{domain}/dns/records", headers=get_headers(), timeout=10)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
        return []
    return r.json().get("data", [])

def add_dns_record(domain, record_type, name, value, ttl=3600):
    payload = {
        "type": record_type,
        "name": name,
        "value": value,
        "ttl": ttl
    }
    r = requests.post(f"{API_BASE}/domains/{domain}/dns/records", headers=get_headers(), json=payload, timeout=10)
    print(f"Add {record_type} ({name}) -> {value}: Status {r.status_code}")
    return r.status_code in [200, 201, 202]

def ensure_cloudflare_email_routing_records(domain="agy.dpdns.org"):
    print(f"Checking DNS records for {domain}...")
    existing = get_domain_records(domain)
    existing_vals = {f"{r.get('type')}:{r.get('value')}" for r in existing}
    
    cf_records = [
        ("MX", "@", "50 route1.mx.cloudflare.net."),
        ("MX", "@", "44 route2.mx.cloudflare.net."),
        ("MX", "@", "95 route3.mx.cloudflare.net."),
        ("TXT", "@", '"v=spf1 include:_spf.mx.cloudflare.net ~all"')
    ]
    
    for r_type, name, val in cf_records:
        key = f"{r_type}:{val}"
        if key in existing_vals:
            print(f"  ✅ {r_type} {val} already present.")
        else:
            print(f"  ➕ Injecting {r_type} {val}...")
            add_dns_record(domain, r_type, name, val)

if __name__ == "__main__":
    domain = sys.argv[1] if len(sys.argv) > 1 else "agy.dpdns.org"
    domains = list_domains()
    print(f"Connected to DigitalPlat API! Account owns {len(domains)} domain(s):")
    for d in domains:
        print(f"  • {d.get('domain')} (Status: {d.get('status')}, Expires: {d.get('expires_at')})")
    
    ensure_cloudflare_email_routing_records(domain)
    print("\nCurrent DNS Zone records:")
    for r in get_domain_records(domain):
        print(f"  - {r.get('type')} {r.get('name')} -> {r.get('value')} (id: {r.get('id')})")
