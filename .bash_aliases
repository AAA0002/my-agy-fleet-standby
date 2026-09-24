# Antigravity 24/7 Persistent Runner (Immune to Termux closure)
alias agy="/home/arif2743/agy_runner.sh"

# Useful Fleet & Bot Management Aliases
alias botlog="tail -f /home/arif2743/userbot.log"
alias superlog="tail -f /home/arif2743/supervisor.log"
alias botstatus="ps aux | grep -E 'python.*userbot|supervisor|tmux' | grep -v grep"
alias botrestart="kill -9 \$(pgrep -f userbot_refresher.py)"
alias botattach="tmux attach -t telegram_bot"
