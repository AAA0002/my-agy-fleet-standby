export const CONFIG = {
  ADMIN_IDS: [6727787768],
  SECRET_KEY: (typeof process !== "undefined" && (process.env?.SECRET_KEY || process.env?.CF_SECRET_KEY)) || "",
  UPSTASH_URL: "https://internal-dodo-83852.upstash.io",
  UPSTASH_TOKEN: (typeof process !== "undefined" && process.env?.UPSTASH_TOKEN) || "",
  WEBAPP_URL: "https://app8858823950.tgcloud.ai/",
  BACKEND_NODES: [
    "https://my-agy-fleet-standby-node3.onrender.com",
    "https://my-agy-fleet-standby-node2.onrender.com"
  ],
  EDGE_MESH: [
    "https://my-agy-fleet-deno.aaa222.deno.net",
    "https://my-agy-fleet-deno2.aaasupporta.deno.net",
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
  ],
  SUPABASE_URL: "https://znbbaozpevurvbfkxakz.supabase.co",
  BETTERSTACK_HEARTBEAT_URL: "https://uptime.betterstack.com/api/v1/heartbeat/bABS7gYDXgHp6H35XGcU7S6p",
  ACTIVE_BOTS: [
    { name: "MRG Miner", symbol: "MRG", bot: "@mrgminerbot", status: "Active" },
    { name: "ATF Miner", symbol: "ATF", bot: "@ATF_AIRDROP_bot", status: "Active" },
    { name: "Victor's Company", symbol: "VICTOR", bot: "@VictorsCompanybot", status: "Active" },
    { name: "Kynex Network", symbol: "KYNEX", bot: "@Kynex_miningbot", status: "Active" },
    { name: "DiggoMiner", symbol: "DIGGO", bot: "@Diggominer_bot", status: "Active" },
    { name: "PepeGram", symbol: "PEPE", bot: "@Pepe_gram_bot", status: "Active" },
    { name: "AdxEarn AI", symbol: "ADX", bot: "@AdxEarnAibot", status: "Active" },
    { name: "Chicken Land", symbol: "EGG", bot: "@ChickenLandBot", status: "Active" }
  ],
  KNOWN_PHONES: {
    1: "+8801317342850",
    2: "+8801943805617",
    3: "+8801790208077",
    4: "+8801575842094",
    5: "+14302084365",
    6: "+8801867539837",
    7: "+8801718056423",
    8: "+8801797795624",
    9: "+8801727651288",
    10: "+8801729892810",
    11: "+8801571089931",
    12: "+8801774578536",
    13: "+8801838268380",
    14: "+918930504750",
    15: "+8801906045479",
    16: "+8801304151082",
    17: "+8801879273559",
    18: "+8801839716506",
    19: "+8801804723069",
    20: "+8801312863569"
  }
};

export const SECRET_KEY = CONFIG.SECRET_KEY;
export const OWNER_ID = "6727787768";
export const CF_WORKER_URLS = CONFIG.EDGE_MESH;
export const RENDER_NODES = CONFIG.BACKEND_NODES;
export const UPSTASH_URL = "https://internal-dodo-83852.upstash.io";
export const UPSTASH_TOKEN = (typeof process !== "undefined" && process.env?.UPSTASH_TOKEN) || "";
export const BROWSER_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
  "Accept": "application/json"
};
