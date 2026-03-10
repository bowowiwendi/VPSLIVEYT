#!/bin/bash
#
# YouTube Live Streaming - Systemd Service Setup
# Script untuk install dan manage systemd service
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/youtube-live-daemon.service"
SYSTEMD_DIR="/etc/systemd/system"

print_status() {
    echo -e "\033[92m✓\033[0m $1"
}

print_error() {
    echo -e "\033[91m✗\033[0m $1"
}

print_info() {
    echo -e "\033[96mℹ\033[0m $1"
}

print_step() {
    echo -e "\n\033[94m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
    echo -e "\033[94m  $1\033[0m"
    echo -e "\033[94m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
}

if [ "$EUID" -ne 0 ]; then 
    print_error "Script ini membutuhkan akses root."
    echo "  Jalankan dengan: sudo $0"
    exit 1
fi

print_step "YouTube Live Daemon - Service Manager"

echo ""
echo "Pilih aksi:"
echo "  1. Install service"
echo "  2. Uninstall service"
echo "  3. Start service"
echo "  4. Stop service"
echo "  5. Restart service"
echo "  6. Check status"
echo "  7. View logs"
echo "  0. Exit"
echo ""

read -p "Pilihan [0-7]: " choice

case $choice in
    1)
        print_step "Installing Service"
        
        # Copy service file
        cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
        print_status "Service file copied to $SYSTEMD_DIR"
        
        # Update WorkingDirectory in service file
        sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" "$SYSTEMD_DIR/youtube-live-daemon.service"
        sed -i "s|/workspaces/VPSLIVEYT/auto_restart_daemon.py|$SCRIPT_DIR/auto_restart_daemon.py|g" "$SYSTEMD_DIR/youtube-live-daemon.service"
        
        # Reload systemd
        systemctl daemon-reload
        print_status "Systemd reloaded"
        
        # Enable service
        systemctl enable youtube-live-daemon
        print_status "Service enabled"
        
        echo ""
        print_info "Service installed successfully!"
        echo ""
        echo "Commands:"
        echo "  sudo systemctl start youtube-live-daemon    - Start service"
        echo "  sudo systemctl stop youtube-live-daemon     - Stop service"
        echo "  sudo systemctl restart youtube-live-daemon  - Restart service"
        echo "  sudo systemctl status youtube-live-daemon   - Check status"
        echo "  journalctl -u youtube-live-daemon -f        - View logs"
        ;;
        
    2)
        print_step "Uninstalling Service"
        
        # Stop and disable
        systemctl stop youtube-live-daemon 2>/dev/null || true
        systemctl disable youtube-live-daemon 2>/dev/null || true
        
        # Remove service file
        rm -f "$SYSTEMD_DIR/youtube-live-daemon.service"
        
        # Reload systemd
        systemctl daemon-reload
        
        # Remove PID file
        rm -f /var/run/youtube_live_daemon.pid
        
        print_status "Service uninstalled successfully!"
        ;;
        
    3)
        print_step "Starting Service"
        systemctl start youtube-live-daemon
        print_status "Service started"
        ;;
        
    4)
        print_step "Stopping Service"
        systemctl stop youtube-live-daemon
        print_status "Service stopped"
        ;;
        
    5)
        print_step "Restarting Service"
        systemctl restart youtube-live-daemon
        print_status "Service restarted"
        ;;
        
    6)
        print_step "Service Status"
        systemctl status youtube-live-daemon --no-pager || true
        ;;
        
    7)
        print_step "Service Logs"
        journalctl -u youtube-live-daemon -n 50 --no-pager
        ;;
        
    0)
        echo "Exit."
        exit 0
        ;;
        
    *)
        print_error "Invalid choice!"
        exit 1
        ;;
esac

echo ""
