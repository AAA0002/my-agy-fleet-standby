// tgcloud/lib/config.js — Centralized configuration for AAA AUTO mesh
export const SECRET_KEY = (typeof process !== "undefined" && (process.env?.SECRET_KEY || process.env?.CF_SECRET_KEY)) || "";
export const OWNER_ID = (typeof process !== "undefined" && process.env?.OWNER_ID) || "6727787768";

export const CF_WORKER_URLS = [
  "https://restore-agy.aaaai2.workers.dev",
  "https://restore-agy.aaa-bot.workers.dev",
  "https://restore-agy.aaa222.workers.dev",
  "https://restore-agy.agorameet.workers.dev",
  "https://restore-agy.aaaai.workers.dev"
];

export const RENDER_NODES = [
  "https://my-agy-fleet-standby-node2.onrender.com"
];

export const UPSTASH_URL = "https://rich-emu-106119.upstash.io";
export const UPSTASH_TOKEN = (typeof process !== "undefined" && process.env?.UPSTASH_TOKEN) || "";

export const BROWSER_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
  "Accept": "application/json"
};
