#!/bin/bash
#
# YouTube Live Streaming - Installation Script
# Script otomatis untuk install semua dependencies
#

set -e

echo "========================================"
echo "  YouTube Live Streaming - Installer"
echo "========================================"
echo ""

# Cek apakah running sebagai root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠ Script ini membutuhkan akses root."
    echo "  Jalankan dengan: sudo ./install.sh"
    exit 1
fi

# Fungsi untuk print status
print_status() {
    echo "✓ $1"
}

print_error() {
    echo "✗ $1"
}

print_step() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Step 1: Update sistem
print_step "Step 1/5: Update dan Upgrade Sistem"
apt update
apt upgrade -y
print_status "Sistem updated"

# Step 2: Install FFmpeg
print_step "Step 2/5: Install FFmpeg"
apt install -y ffmpeg
ffmpeg -version | head -1
print_status "FFmpeg installed"

# Step 3: Install tmux
print_step "Step 3/5: Install tmux"
apt install -y tmux
tmux -V
print_status "tmux installed"

# Step 4: Install Python3 dan pip
print_step "Step 4/5: Install Python3 & pip"
apt install -y python3 python3-pip
python3 --version
pip3 --version
print_status "Python3 & pip installed"

# Step 5: Install gdown dan Flask
print_step "Step 5/5: Install Python Packages"
pip3 install gdown flask
gdown --version 2>/dev/null || echo "gdown installed"
print_status "gdown and Flask installed"

# Create log directory
print_step "Setup Log Directory"
mkdir -p /var/log/youtube_live
chmod 755 /var/log/youtube_live
print_status "Log directory created: /var/log/youtube_live"

# Set permission untuk script
print_step "Setup Permissions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/youtube_live.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/cli_menu.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/monitor.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/auto_restart_daemon.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/setup_service.sh" 2>/dev/null || true
print_status "Script permissions set"

# Create required directories
print_step "Create Directories"
mkdir -p /var/run
print_status "Directories created"

# Summary
echo ""
echo "========================================"
echo "  ✓ Instalasi Selesai!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Setup konfigurasi:"
echo "     python3 youtube_live.py setup -k YOUR_STREAM_KEY"
echo ""
echo "  2. Mulai streaming:"
echo "     python3 youtube_live.py start"
echo ""
echo "  3. Monitor status:"
echo "     python3 youtube_live.py status"
echo ""
echo "  4. Download video dari Google Drive:"
echo "     python3 youtube_live.py download https://drive.google.com/uc?id=YOUR_FILE_ID"
echo ""
echo "  5. Setup auto-restart daemon (optional):"
echo "     sudo ./setup_service.sh"
echo ""
echo "========================================"
