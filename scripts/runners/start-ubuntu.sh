#!/data/data/com.termux/files/usr/bin/bash
# Launch Ubuntu interactive shell with full Termux project bound to /root/workspace
echo "🚀 Starting Ubuntu (glibc environment)..."
proot-distro login ubuntu --bind /data/data/com.termux/files/home:/root/workspace --work-dir /root/workspace
