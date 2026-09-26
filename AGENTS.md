# Antigravity Rules & Directives for AAA AUTO

## 1. 🛡️ Strict Project Isolation
- **No Cross-Project Contamination**: Never mix code, configurations, packages, or context from `/root/projects/AAA` or other projects into this workspace.
- **Separate Bot Isolation**: `@AAATelegramIdBot` (repository `AAA2743/AA`) is a completely distinct project and must never be touched, modified, or merged into `AAA_AUTO`.
- **Self-Contained**: Everything relating to this project must remain strictly within `/root/projects/AAA_AUTO`.
- **Clean Boundaries**: Never modify system or other workspace files unless explicitly requested.

---

## 2. 📝 Persistent Action Memory & Change Audit
- **Full Action Transparency**: Always maintain a clear record of:
  - **What was done**: Completed features, installed packages, and configuration updates.
  - **What is currently in progress**: The specific task being solved right now.
  - **What was modified or removed**: Explicitly state any file, function, or line of code that is deleted or refactored, along with the reason.
- **Project Changelog**: Maintain a clean, human-readable `CHANGELOG.md` in the repository tracking all major additions, edits, and deletions.
- **Walrus Memory Sync**: Proactively save key architectural decisions and user preferences to Walrus Memory so context is preserved permanently across restarts.

---

## 3. 🎨 Quality Standards & Open-Source UI Excellence
- **No Throwaway or Useless Apps**: Do not build generic, half-baked, or useless toy mockups. Build production-grade, intentional, and useful solutions.
- **Beautiful, Modern UI Reference**:
  - When designing interfaces or websites, reference modern, battle-tested open-source designs from GitHub and the open-source community (e.g., Tailwind CSS, shadcn/ui design patterns, modern clean component architecture).
  - Prioritize mobile responsiveness, sleek aesthetics, clean typography, and intuitive UX suitable for smartphone and desktop screens.

---

## 4. 📱 Zero Phone Load Directive (Samsung Galaxy A30)
- **Phone Exclusivity**: The Samsung Galaxy A30 is STRICTLY dedicated to running the Antigravity AI CLI for pair programming.
- **ZERO Bots on Phone**: NEVER run bots, daemon loops, supervisor loops, scrapers, queue pollers, or MTProto relay listeners on the phone under ANY circumstances.
- **100% Cloud-First**: All bot listeners, farming cycles, token refreshers, and MTProto logins MUST run 100% in the cloud (Cloudflare Workers, Render, Deno, Vercel).
- **Hard Resource Guardrail**: Terminate and prevent any background Python bot processes from running locally. Keep RAM and CPU entirely free for the AI coding session.
- **Git Checkpoints**: Always keep Git history clean and run checkpoints regularly so no progress is lost if the mobile session drops.

---

## 5. ☁️ Zero-Trust Ephemeral Infrastructure ("Never Trust VPS or Local")
- **Ephemeral Mindset**: Always assume any VPS or local machine can die, expire, or get wiped at any moment without warning.
- **Continuous Off-Machine Durability**:
  - Keep automated disaster recovery archives flowing to the Telegram vault (`@myagyai`) via `backup_manager.py`.
  - Replicate state, heartbeat sentinel, and telemetry across the 3-node Cloudflare Edge mesh.
  - Regularly sync critical architectural decisions and state to Walrus Memory.
  - Keep Git checkpoints clean and documented in `CHANGELOG.md`.
- **1-Click Disaster Recovery**: Ensure the self-contained 1-click restore mechanism (`restore.sh` / Telegram one-liner) always works out-of-the-box anywhere.
