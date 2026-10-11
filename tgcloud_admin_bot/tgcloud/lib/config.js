export const CONFIG = {
  ADMIN_IDS: [6727787768],
  SECRET_KEY: "agy_cf_secret_7d36994e_2026",
  BACKEND_NODES: [
    "https://my-agy-fleet-standby-node2.onrender.com",
    "https://my-agy-fleet-standby-node3.onrender.com",
    "https://my-agy-fleet-standby.onrender.com"
  ],
  EDGE_MESH: [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
  ],
  ACTIVE_BOTS: [
    { name: "Stones Miner", symbol: "STONES", status: "Active" },
    { name: "MRG Miner", symbol: "MRG", status: "Active" },
    { name: "AI Lab", symbol: "AILAB", status: "Active" },
    { name: "UltraWallet", symbol: "ULTRA", status: "Active" },
    { name: "ATF Miner", symbol: "ATF", status: "Active" },
    { name: "FINVORA", symbol: "FINVORA", status: "Active" },
    { name: "Victor's Company", symbol: "VICTOR", status: "Active" },
    { name: "VyroDrop", symbol: "VYRO", status: "Active" }
  ],
  KNOWN_PHONES: {
    1: "+8801317342850",
    2: "+8801943805617",
    3: "+8801790208077",
    4: "+8801861036830",
    5: "+8801790208099",
    6: "+8801750275811",
    7: "+8801736652150",
    8: "+8801752495911",
    9: "+8801716942761",
    10: "+8801777264871",
    11: "+8801790208066",
    12: "+8801752763781",
    13: "+8801867160751",
    14: "+8801764654522",
    15: "+8801742445831",
    16: "+8801729606688",
    17: "+8801725579294",
    18: "+8801728148811"
  }
};

export const SECRET_KEY = CONFIG.SECRET_KEY;
export const OWNER_ID = "6727787768";
export const CF_WORKER_URLS = CONFIG.EDGE_MESH;
export const RENDER_NODES = CONFIG.BACKEND_NODES;
export const UPSTASH_URL = "https://pleasant-locust-220893.upstash.io";
export const UPSTASH_TOKEN = "gQAAAAAAA17dAAIgcDFhZmU2OTdiZjRmYmY0OTI2OTgyZTYyYjkwYWQ5ODYzZg";
export const BROWSER_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
  "Accept": "application/json"
};
