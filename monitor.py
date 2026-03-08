#!/usr/bin/env python3
"""
YouTube Live Streaming - Monitoring Dashboard
Dashboard real-time untuk monitor live streaming dengan tampilan yang lebih baik.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path.home() / ".youtube_live_config.json"
LOG_DIR = Path("/var/log/youtube_live")


class Colors:
    """ANSI color codes untuk terminal."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"


def clear_screen():
    """Clear terminal screen."""
    os.system("clear" if os.name != "nt" else "cls")


def get_config():
    """Load konfigurasi."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stream_key": "", "video_path": "/root/live.mp4", "session_name": "youtube_live"}


def get_session_status(session_name):
    """Cek apakah sesi tmux aktif."""
    try:
        result = subprocess.run(
            f"tmux list-sessions 2>/dev/null | grep -E '^{session_name}:'",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            return True, result.stdout.strip()
        return False, ""
    except Exception:
        return False, ""


def get_process_info():
    """Dapatkan info proses FFmpeg yang sedang berjalan."""
    try:
        result = subprocess.run(
            "ps aux | grep '[f]fmpeg' | head -5",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_system_stats():
    """Dapatkan statistik sistem (CPU, Memory, Disk)."""
    stats = {}
    
    # CPU Usage
    try:
        result = subprocess.run(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'",
            shell=True,
            capture_output=True,
            text=True
        )
        stats["cpu"] = float(result.stdout.strip()) if result.stdout.strip() else 0
    except Exception:
        stats["cpu"] = 0
    
    # Memory Usage
    try:
        result = subprocess.run(
            "free -m | awk 'NR==2{printf \"%.1f/%.1f MB (%.1f%%)\", $3,$2,$3*100/$2}'",
            shell=True,
            capture_output=True,
            text=True
        )
        stats["memory"] = result.stdout.strip()
    except Exception:
        stats["memory"] = "N/A"
    
    # Disk Usage
    try:
        result = subprocess.run(
            "df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'",
            shell=True,
            capture_output=True,
            text=True
        )
        stats["disk"] = result.stdout.strip()
    except Exception:
        stats["disk"] = "N/A"
    
    # Network (upload)
    try:
        result = subprocess.run(
            "cat /proc/net/dev | grep -E 'eth0|ens' | awk '{print $9}'",
            shell=True,
            capture_output=True,
            text=True
        )
        stats["network_tx"] = result.stdout.strip()
    except Exception:
        stats["network_tx"] = "N/A"
    
    return stats


def get_recent_logs(session_name, lines=10):
    """Ambil log terbaru."""
    if not LOG_DIR.exists():
        return []
    
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    if logs:
        # Cari log yang sesuai dengan session
        for log in logs:
            if session_name in log.name:
                try:
                    with open(log, "r") as f:
                        return f.readlines()[-lines:]
                except Exception:
                    pass
        
        # Jika tidak ada yang cocok, ambil yang terbaru
        try:
            with open(logs[0], "r") as f:
                return f.readlines()[-lines:]
        except Exception:
            pass
    
    return []


def format_uptime(seconds):
    """Format uptime dalam format yang mudah dibaca."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_session_uptime(session_name):
    """Estimasi uptime sesi."""
    try:
        result = subprocess.run(
            f"tmux list-sessions -F '#{{session_name}}:#{{session_created}}' 2>/dev/null | grep '^{session_name}:'",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            parts = result.stdout.strip().split(":")
            if len(parts) >= 2:
                created = int(parts[1])
                uptime = time.time() - created
                return format_uptime(uptime)
    except Exception:
        pass
    return "N/A"


def draw_dashboard(config, running, session_info, system_stats, logs):
    """Gambar dashboard di terminal."""
    session_name = config.get("session_name", "youtube_live")
    
    # Header
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "📺 YOUTUBE LIVE MONITORING DASHBOARD" + " " * 12 + "║")
    print("╚" + "═" * 58 + "╝")
    print(f"{Colors.RESET}")
    
    # Status Section
    print(f"{Colors.BOLD}┌─ Streaming Status ─────────────────────────────────────┐{Colors.RESET}")
    
    if running:
        status_text = f"{Colors.BG_GREEN}{Colors.BOLD} 🟢 LIVE {Colors.RESET}"
        uptime = get_session_uptime(session_name)
        print(f"│  Status   : {status_text}  Uptime: {Colors.GREEN}{uptime}{Colors.RESET}                    │")
    else:
        status_text = f"{Colors.BG_RED}{Colors.BOLD} ⚫ OFFLINE {Colors.RESET}"
        print(f"│  Status   : {status_text}                                          │")
    
    print(f"│  Session  : {session_name:<47}│")
    print(f"└──────────────────────────────────────────────────────────────┘")
    
    # System Stats Section
    print(f"{Colors.BOLD}┌─ System Resources ─────────────────────────────────────┐{Colors.RESET}")
    print(f"│  CPU     : {system_stats.get('cpu', 0):>6.1f}% {'█' * int(system_stats.get('cpu', 0) / 5):<20}                    │")
    
    memory = system_stats.get("memory", "N/A")
    print(f"│  Memory  : {memory:<52}│")
    
    disk = system_stats.get("disk", "N/A")
    print(f"│  Disk    : {disk:<52}│")
    print(f"└──────────────────────────────────────────────────────────────┘")
    
    # Config Section
    print(f"{Colors.BOLD}┌─ Configuration ────────────────────────────────────────┐{Colors.RESET}")
    video_path = config.get("video_path", "/root/live.mp4")
    stream_key = config.get("stream_key", "")
    key_status = "✓ Set" if stream_key else f"{Colors.RED}✗ Not Set{Colors.RESET}"
    
    print(f"│  Video   : {video_path:<52}│")
    print(f"│  Stream  : {key_status:<52}│")
    print(f"└──────────────────────────────────────────────────────────────┘")
    
    # Process Info
    print(f"{Colors.BOLD}┌─ Active FFmpeg Processes ──────────────────────────────┐{Colors.RESET}")
    process_info = get_process_info()
    if process_info:
        for line in process_info.split("\n")[:3]:
            truncated = line[:60]
            print(f"│  {truncated:<60}│")
    else:
        print(f"│  No active FFmpeg processes                              │")
    print(f"└──────────────────────────────────────────────────────────────┘")
    
    # Recent Logs
    print(f"{Colors.BOLD}┌─ Recent Logs (Last 10 lines) ────────────────────────────┐{Colors.RESET}")
    if logs:
        for log in logs:
            truncated = log.strip()[:60]
            print(f"│  {truncated:<60}│")
    else:
        print(f"│  No logs available                                       │")
    print(f"└──────────────────────────────────────────────────────────────┘")
    
    # Quick Commands
    print(f"{Colors.BOLD}┌─ Quick Commands ───────────────────────────────────────┐{Colors.RESET}")
    print(f"│  {Colors.YELLOW}[S]{Colors.RESET}tart  {Colors.YELLOW}[P]{Colors.RESET}ause  {Colors.YELLOW}[R]{Colors.RESET}estart  {Colors.YELLOW}[Q]{Colors.RESET}uit  {Colors.YELLOW}[L]{Colors.RESET}ogs  {Colors.YELLOW}[C]{Colors.RESET}lear              │")
    print(f"└──────────────────────────────────────────────────────────────┘")
    
    # Footer
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{Colors.WHITE}Last updated: {timestamp}{Colors.RESET}")


def interactive_monitor():
    """Interactive monitoring mode."""
    config = get_config()
    session_name = config.get("session_name", "youtube_live")
    
    print(f"{Colors.CYAN}Starting interactive monitor for session: {session_name}{Colors.RESET}")
    print(f"{Colors.YELLOW}Press 'q' to quit{Colors.RESET}\n")
    time.sleep(1)
    
    try:
        while True:
            clear_screen()
            
            running, session_info = get_session_status(session_name)
            system_stats = get_system_stats()
            logs = get_recent_logs(session_name)
            
            draw_dashboard(config, running, session_info, system_stats, logs)
            
            # Non-blocking input check
            import select
            import tty
            import termios
            
            # Set terminal to non-blocking
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                tty.setcbreak(fd)
                
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 'q':
                        break
                    elif key == 's':
                        # Start command
                        subprocess.run(["python3", "/workspaces/VPSLIVEYT/youtube_live.py", "start"])
                        time.sleep(2)
                    elif key == 'p':
                        # Pause (not implemented, just info)
                        print("\nPause not directly supported. Use 'stop' to end stream.")
                        time.sleep(1)
                    elif key == 'r':
                        # Restart
                        subprocess.run(["python3", "/workspaces/VPSLIVEYT/youtube_live.py", "stop"])
                        time.sleep(1)
                        subprocess.run(["python3", "/workspaces/VPSLIVEYT/youtube_live.py", "start"])
                        time.sleep(2)
                    elif key == 'l':
                        # Show full logs
                        if LOG_DIR.exists():
                            logs = sorted(LOG_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
                            if logs:
                                print(f"\nOpening log: {logs[0]}")
                                subprocess.run(["tail", "-50", str(logs[0])])
                                input("\nPress Enter to continue...")
                    elif key == 'c':
                        clear_screen()
            except Exception:
                pass
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    
    print(f"\n{Colors.GREEN}✓ Monitoring stopped.{Colors.RESET}")


def simple_monitor():
    """Simple text-based monitoring (fallback)."""
    config = get_config()
    session_name = config.get("session_name", "youtube_live")
    
    print(f"Monitoring session: {session_name}")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            running, session_info = get_session_status(session_name)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if running:
                uptime = get_session_uptime(session_name)
                print(f"[{timestamp}] {Colors.GREEN}🟢 LIVE{Colors.RESET} | Uptime: {uptime}", end="\r")
            else:
                print(f"[{timestamp}] {Colors.RED}⚫ OFFLINE{Colors.RESET}                            ", end="\r")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Live Streaming Monitor")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Interactive mode dengan keyboard shortcuts")
    parser.add_argument("-n", "--name", help="Session name untuk monitor")
    parser.add_argument("--menu", action="store_true",
                        help="Show menu with back option")
    args = parser.parse_args()

    config = get_config()
    if args.name:
        config["session_name"] = args.name

    if args.menu:
        # Show menu with back option
        while True:
            clear_screen()
            print(f"{Colors.CYAN}{Colors.BOLD}")
            print("╔" + "═" * 58 + "╗")
            print("║" + " " * 15 + "🔍 MONITORING MENU" + " " * 23 + "║")
            print("╚" + "═" * 58 + "╝")
            print(f"{Colors.RESET}")
            
            running, _ = get_session_status(config.get("session_name", "youtube_live"))
            status = f"{Colors.GREEN}🟢 LIVE{Colors.RESET}" if running else f"{Colors.RED}⚫ OFFLINE{Colors.RESET}"
            
            print(f"  Session: {config.get('session_name', 'youtube_live')}")
            print(f"  Status : {status}")
            print()
            print("  1. Start Monitoring")
            print("  2. Interactive Dashboard")
            print("  0. Back to Main Menu")
            print()
            
            choice = input(f"{Colors.YELLOW}  Pilihan: {Colors.RESET}").strip()
            
            if choice == "1":
                simple_monitor()
            elif choice == "2":
                if sys.stdin.isatty():
                    interactive_monitor()
                else:
                    print("Interactive mode requires a TTY.")
                    time.sleep(1)
            elif choice == "0":
                # Launch main menu
                subprocess.run(["python3", str(Path(__file__).parent / "cli_menu.py")])
                break
    elif args.interactive:
        # Cek apakah terminal mendukung
        if sys.stdin.isatty():
            interactive_monitor()
        else:
            print("Interactive mode requires a TTY. Using simple mode instead.")
            simple_monitor()
    else:
        simple_monitor()


if __name__ == "__main__":
    main()
