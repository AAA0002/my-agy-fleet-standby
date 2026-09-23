# Antigravity Rules & Directives for AAA AUTO

## 1. 🛡️ Strict Project Isolation
- **No Cross-Project Contamination**: Never mix code, configurations, packages, or context from `/root/projects/AAA` or other projects into this workspace.
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

## 4. 📱 Mobile Performance Guardrails (Samsung Galaxy A30)
- **Lean Footprint**: Keep memory usage low. Avoid heavy memory-hungry dev servers or massive node_modules bloat.
- **Git Checkpoints**: Always keep Git history clean and run checkpoints regularly so no progress is lost if the mobile session drops.
