#!/usr/bin/env python3
"""
YouTube Live Streaming - Interactive CLI Menu
Menu interaktif untuk mengelola live streaming dengan mudah.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path.home() / ".youtube_live_config.json"
MULTI_CONFIG_FILE = Path.home() / ".youtube_live_multi_config.json"
AUTO_RESTART_FILE = Path.home() / ".youtube_live_auto_restart.json"
LOG_DIR = Path("/var/log/youtube_live")

# RTMP URLs untuk berbagai platform
RTMP_PLATFORMS = {
    "youtube": "rtmp://a.rtmp.youtube.com/live2",
    "youtube_secondary": "rtmp://b.rtmp.youtube.com/live2",
    "facebook": "rtmps://live-api-s.facebook.com:443/rtmp",
    "twitch": "rtmp://live.twitch.tv/app",
    "tiktok": "rtmp://push.tiktok.com/live",
    "custom": ""
}


class Colors:
    """ANSI color codes."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"


def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")


def print_header(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}\n")


def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}┌─ {title} {'─' * (50 - len(title))}{Colors.RESET}")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stream_key": "", "video_path": "/root/live.mp4", "session_name": "youtube_live"}


def save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_multi_config():
    if MULTI_CONFIG_FILE.exists():
        with open(MULTI_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"streams": []}


def save_multi_config(config):
    MULTI_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MULTI_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_auto_restart_config():
    """Load auto-restart konfigurasi."""
    if AUTO_RESTART_FILE.exists():
        with open(AUTO_RESTART_FILE, "r") as f:
            return json.load(f)
    return {"enabled": False, "interval_hours": 6}


def save_auto_restart_config(config):
    """Simpan auto-restart konfigurasi."""
    AUTO_RESTART_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTO_RESTART_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_session_status(session_name):
    try:
        result = subprocess.run(
            f"tmux list-sessions 2>/dev/null | grep -E '^{session_name}:'",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip() != ""
    except Exception:
        return False


def get_all_streaming_sessions():
    """Dapatkan semua sesi streaming yang aktif."""
    try:
        result = subprocess.run(
            "tmux list-sessions 2>/dev/null",
            shell=True,
            capture_output=True,
            text=True
        )
        sessions = []
        for line in result.stdout.strip().split("\n"):
            if line:
                sessions.append(line.split(":")[0])
        return sessions
    except Exception:
        return []


def check_dependencies():
    deps = {
        "ffmpeg": "ffmpeg -version",
        "tmux": "tmux -V",
        "python3": "python3 --version",
    }
    
    missing = []
    for name, cmd in deps.items():
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing.append(name)
    
    if missing:
        print_error(f"Dependencies missing: {', '.join(missing)}")
        return False
    return True


# ==================== MENU FUNCTIONS ====================

def menu_setup():
    """Setup configuration menu."""
    clear_screen()
    print_header("📋 SETUP KONFIGURASI")
    
    config = load_config()
    
    print_section("Konfigurasi Saat Ini")
    print(f"  Stream Key     : {'****' + config.get('stream_key', '')[-4:] if config.get('stream_key') else Colors.RED + 'Belum disetel' + Colors.RESET}")
    print(f"  Video Path     : {config.get('video_path', '/root/live.mp4')}")
    print(f"  Session Name   : {config.get('session_name', 'youtube_live')}")
    
    print_section("Setup Options")
    print("  1. Set Stream Key")
    print("  2. Set Video Path")
    print("  3. Set Session Name")
    print("  4. Setup Lengkap")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        key = input("  Stream Key: ").strip()
        if key:
            config["stream_key"] = key
            save_config(config)
            print_success("Stream Key disimpan!")
    
    elif choice == "2":
        path = input("  Video Path [/root/live.mp4]: ").strip()
        if path:
            config["video_path"] = path
            save_config(config)
            print_success("Video Path disimpan!")
    
    elif choice == "3":
        name = input("  Session Name [youtube_live]: ").strip()
        if name:
            config["session_name"] = name
            save_config(config)
            print_success("Session Name disimpan!")
    
    elif choice == "4":
        print("\n  Setup Lengkap:")
        key = input("    Stream Key: ").strip()
        path = input("    Video Path [/root/live.mp4]: ").strip() or "/root/live.mp4"
        name = input("    Session Name [youtube_live]: ").strip() or "youtube_live"
        
        config = {"stream_key": key, "video_path": path, "session_name": name}
        save_config(config)
        print_success("Konfigurasi lengkap disimpan!")
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_single_stream():
    """Start single stream menu."""
    clear_screen()
    print_header("🔴 START SINGLE STREAM")
    
    config = load_config()
    
    print_section("Konfigurasi")
    print(f"  Video Path   : {config.get('video_path', '/root/live.mp4')}")
    print(f"  Session Name : {config.get('session_name', 'youtube_live')}")
    print(f"  Stream Key   : {'****' + config.get('stream_key', '')[-4:] if config.get('stream_key') else Colors.RED + 'Belum disetel' + Colors.RESET}")
    
    # Cek video file
    video_path = config.get("video_path", "/root/live.mp4")
    if not Path(video_path).exists():
        print_warning(f"Video file tidak ditemukan: {video_path}")
    
    print_section("Options")
    print("  1. Start Streaming (Continuous)")
    print("  2. Start Streaming dengan Timeout")
    print("  3. Start dengan Video Custom")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        if not config.get("stream_key"):
            print_error("Stream Key belum disetel! Setup dulu.")
        else:
            cmd = f"python3 youtube_live.py start"
            subprocess.run(cmd, shell=True)
    
    elif choice == "2":
        duration = input("  Durasi (jam) [10]: ").strip() or "10"
        if not config.get("stream_key"):
            print_error("Stream Key belum disetel!")
        else:
            cmd = f"python3 youtube_live.py start -d {duration}"
            subprocess.run(cmd, shell=True)
    
    elif choice == "3":
        custom_path = input("  Video Path: ").strip()
        if custom_path and Path(custom_path).exists():
            cmd = f"python3 youtube_live.py start -v {custom_path}"
            subprocess.run(cmd, shell=True)
        else:
            print_error("Video file tidak ditemukan!")
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_multi_stream():
    """Multi-streaming configuration menu."""
    clear_screen()
    print_header("📡 MULTI-STREAMING SETUP")
    
    multi_config = load_multi_config()
    streams = multi_config.get("streams", [])
    
    print_section("Active Multi-Streams")
    if streams:
        for i, stream in enumerate(streams, 1):
            platform = stream.get("platform", "custom")
            session = stream.get("session_name", f"stream_{i}")
            status = "🟢 LIVE" if get_session_status(session) else "⚫ OFFLINE"
            print(f"  {i}. {platform.upper():<12} | Session: {session:<20} | {status}")
    else:
        print("  Belum ada multi-stream configuration")
    
    print_section("Multi-Stream Options")
    print("  1. Add Stream (YouTube)")
    print("  2. Add Stream (Facebook)")
    print("  3. Add Stream (Twitch)")
    print("  4. Add Stream (TikTok)")
    print("  5. Add Stream (Custom RTMP)")
    print("  6. Start All Streams")
    print("  7. Stop All Streams")
    print("  8. Remove Stream")
    print("  9. Clear All")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        name = input("  Session Name [youtube_multi_1]: ").strip() or "youtube_multi_1"
        key = input("  Stream Key: ").strip()
        if key:
            streams.append({
                "platform": "youtube",
                "session_name": name,
                "stream_key": key,
                "rtmp_url": RTMP_PLATFORMS["youtube"]
            })
            save_multi_config({"streams": streams})
            print_success(f"Stream '{name}' ditambahkan!")
    
    elif choice == "2":
        name = input("  Session Name [facebook_live]: ").strip() or "facebook_live"
        key = input("  Stream Key: ").strip()
        if key:
            streams.append({
                "platform": "facebook",
                "session_name": name,
                "stream_key": key,
                "rtmp_url": RTMP_PLATFORMS["facebook"]
            })
            save_multi_config({"streams": streams})
            print_success(f"Stream '{name}' ditambahkan!")
    
    elif choice == "3":
        name = input("  Session Name [twitch_stream]: ").strip() or "twitch_stream"
        key = input("  Stream Key: ").strip()
        if key:
            streams.append({
                "platform": "twitch",
                "session_name": name,
                "stream_key": key,
                "rtmp_url": RTMP_PLATFORMS["twitch"]
            })
            save_multi_config({"streams": streams})
            print_success(f"Stream '{name}' ditambahkan!")
    
    elif choice == "4":
        name = input("  Session Name [tiktok_live]: ").strip() or "tiktok_live"
        key = input("  Stream Key: ").strip()
        if key:
            streams.append({
                "platform": "tiktok",
                "session_name": name,
                "stream_key": key,
                "rtmp_url": RTMP_PLATFORMS["tiktok"]
            })
            save_multi_config({"streams": streams})
            print_success(f"Stream '{name}' ditambahkan!")
    
    elif choice == "5":
        name = input("  Session Name [custom_stream]: ").strip() or "custom_stream"
        rtmp = input("  RTMP URL: ").strip()
        key = input("  Stream Key: ").strip()
        if rtmp and key:
            streams.append({
                "platform": "custom",
                "session_name": name,
                "stream_key": key,
                "rtmp_url": rtmp
            })
            save_multi_config({"streams": streams})
            print_success(f"Stream '{name}' ditambahkan!")
    
    elif choice == "6":
        if not streams:
            print_error("Tidak ada stream yang dikonfigurasi!")
        else:
            config = load_config()
            video_path = config.get("video_path", "/root/live.mp4")
            
            print_warning(f"Starting {len(streams)} streams...")
            for stream in streams:
                session = stream["session_name"]
                if get_session_status(session):
                    print_warning(f"  {session} sudah berjalan, skip...")
                else:
                    cmd = (
                        f"ffmpeg -stream_loop -1 -re -i {video_path} "
                        f"-f flv -c:v copy -c:a copy "
                        f"{stream['rtmp_url']}/{stream['stream_key']} "
                        f"2>&1 | tee -a /var/log/youtube_live/{session}.log"
                    )
                    tmux_cmd = f"tmux new -d -s {session} '{cmd}'"
                    subprocess.run(tmux_cmd, shell=True)
                    print_success(f"  Started: {session} ({stream['platform']})")
            
            print_success("All streams started!")
    
    elif choice == "7":
        if not streams:
            print_error("Tidak ada stream yang dikonfigurasi!")
        else:
            for stream in streams:
                session = stream["session_name"]
                subprocess.run(f"tmux kill-session -t {session} 2>/dev/null", shell=True)
                print_success(f"  Stopped: {session}")
            print_success("All streams stopped!")
    
    elif choice == "8":
        if streams:
            print("  Streams:")
            for i, stream in enumerate(streams, 1):
                print(f"    {i}. {stream['platform']} - {stream['session_name']}")
            idx = input("  Stream to remove (number): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(streams):
                removed = streams.pop(int(idx) - 1)
                save_multi_config({"streams": streams})
                print_success(f"Stream '{removed['session_name']}' dihapus!")
    
    elif choice == "9":
        confirm = input("  Clear all streams? (y/n): ").strip().lower()
        if confirm == "y":
            save_multi_config({"streams": []})
            print_success("All configurations cleared!")
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_status():
    """Status display menu."""
    clear_screen()
    print_header("📊 STREAMING STATUS")
    
    config = load_config()
    multi_config = load_multi_config()
    
    print_section("Single Stream Config")
    session_name = config.get("session_name", "youtube_live")
    is_live = get_session_status(session_name)
    status = f"{Colors.GREEN}🟢 LIVE{Colors.RESET}" if is_live else f"{Colors.RED}⚫ OFFLINE{Colors.RESET}"
    print(f"  Session: {session_name}")
    print(f"  Status : {status}")
    print(f"  Video  : {config.get('video_path', '/root/live.mp4')}")
    
    print_section("Multi-Stream Status")
    streams = multi_config.get("streams", [])
    if streams:
        for stream in streams:
            session = stream["session_name"]
            is_live = get_session_status(session)
            status = f"{Colors.GREEN}🟢 LIVE{Colors.RESET}" if is_live else f"{Colors.RED}⚫ OFFLINE{Colors.RESET}"
            print(f"  {stream['platform'].upper():<12} | {session:<20} | {status}")
    else:
        print("  No multi-stream configured")
    
    print_section("All Active TMUX Sessions")
    sessions = get_all_streaming_sessions()
    if sessions:
        for session in sessions:
            print(f"  • {session}")
    else:
        print("  No active sessions")
    
    print_section("Recent Logs")
    if LOG_DIR.exists():
        logs = sorted(LOG_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        for log in logs:
            print(f"  📄 {log.name} ({log.stat().st_size} bytes)")
    else:
        print("  No logs available")
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_monitor():
    """Real-time monitoring menu."""
    clear_screen()
    print_header("🔍 REAL-TIME MONITOR")

    config = load_config()
    session_name = config.get("session_name", "youtube_live")

    print(f"  Session: {session_name}")
    print()
    print("  1. Start Simple Monitor")
    print("  2. Interactive Dashboard")
    print("  0. Kembali")
    print()
    
    choice = input(f"{Colors.YELLOW}  Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        print(f"\n  Monitoring: {session_name}")
        print(f"  Press Ctrl+C to stop\n")
        try:
            while True:
                is_live = get_session_status(session_name)
                timestamp = datetime.now().strftime("%H:%M:%S")
                if is_live:
                    status = f"{Colors.GREEN}🟢 LIVE{Colors.RESET}"
                else:
                    status = f"{Colors.RED}⚫ OFFLINE{Colors.RESET}"
                print(f"[{timestamp}] {status}", end="\r")
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}✓ Monitoring stopped.{Colors.RESET}")
    
    elif choice == "2":
        # Launch interactive monitor
        subprocess.run(["python3", str(Path(__file__).parent / "monitor.py"), "-i"])
    
    # Returns to main menu automatically


def menu_stop():
    """Stop streaming menu."""
    clear_screen()
    print_header("⏹️ STOP STREAMING")
    
    print_section("Select Stream to Stop")
    print("  1. Stop Single Stream (default session)")
    print("  2. Stop Specific Session")
    print("  3. Stop All Streaming Sessions")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        config = load_config()
        session = config.get("session_name", "youtube_live")
        subprocess.run(f"tmux kill-session -t {session}", shell=True)
        print_success(f"Stream '{session}' stopped!")
    
    elif choice == "2":
        sessions = get_all_streaming_sessions()
        if sessions:
            print("  Active sessions:")
            for i, s in enumerate(sessions, 1):
                print(f"    {i}. {s}")
            idx = input("  Select (number): ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(sessions):
                session = sessions[int(idx) - 1]
                subprocess.run(f"tmux kill-session -t {session}", shell=True)
                print_success(f"Stream '{session}' stopped!")
        else:
            print_warning("No active sessions!")
    
    elif choice == "3":
        sessions = get_all_streaming_sessions()
        if sessions:
            confirm = input(f"  Stop {len(sessions)} sessions? (y/n): ").strip().lower()
            if confirm == "y":
                for session in sessions:
                    subprocess.run(f"tmux kill-session -t {session}", shell=True)
                    print_success(f"  Stopped: {session}")
                print_success("All streams stopped!")
        else:
            print_warning("No active sessions!")
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_download():
    """Download from Google Drive menu."""
    clear_screen()
    print_header("📥 DOWNLOAD FROM GOOGLE DRIVE")
    
    print_section("Download Options")
    print("  1. Download with gdown")
    print("  2. Set as Default Video")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        url = input("  Google Drive URL: ").strip()
        if url:
            output = input("  Output path (optional): ").strip()
            cmd = f"gdown {url}"
            if output:
                cmd += f" -O {output}"
            subprocess.run(cmd, shell=True)
    
    elif choice == "2":
        url = input("  Google Drive URL: ").strip()
        if url:
            output = input("  Save as [/root/live.mp4]: ").strip() or "/root/live.mp4"
            cmd = f"gdown {url} -O {output}"
            subprocess.run(cmd, shell=True)
            
            config = load_config()
            config["video_path"] = output
            save_config(config)
            print_success(f"Video path set to: {output}")
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_auto_restart():
    """Auto-restart configuration menu."""
    clear_screen()
    print_header("⏰ AUTO-RESTART CONFIGURATION")
    
    auto_config = load_auto_restart_config()
    
    print_section("Current Status")
    status = f"{Colors.GREEN}✓ Enabled{Colors.RESET}" if auto_config.get("enabled") else f"{Colors.RED}✗ Disabled{Colors.RESET}"
    print(f"  Status   : {status}")
    print(f"  Interval : {auto_config.get('interval_hours', 6)} jam")
    
    print_section("Auto-Restart Options")
    print("  1. Enable Auto-Restart")
    print("  2. Disable Auto-Restart")
    print("  3. Set Interval")
    print("  4. Restart Now (Manual)")
    print("  5. Start Daemon (Background)")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        interval = input(f"  Interval (jam) [{auto_config.get('interval_hours', 6)}]: ").strip()
        if interval.isdigit():
            save_auto_restart_config({"enabled": True, "interval_hours": int(interval)})
            print_success("Auto-restart enabled!")
        else:
            save_auto_restart_config({"enabled": True, "interval_hours": auto_config.get('interval_hours', 6)})
            print_success("Auto-restart enabled!")
    
    elif choice == "2":
        save_auto_restart_config({"enabled": False, "interval_hours": auto_config.get('interval_hours', 6)})
        print_success("Auto-restart disabled!")
    
    elif choice == "3":
        interval = input("  Interval (jam): ").strip()
        if interval.isdigit():
            save_auto_restart_config({"enabled": auto_config.get("enabled", False), "interval_hours": int(interval)})
            print_success(f"Interval set to {interval} jam!")
    
    elif choice == "4":
        print_info("Restarting all streams...")
        subprocess.run(["python3", str(Path(__file__).parent / "youtube_live.py"), "auto-restart-now"])
    
    elif choice == "5":
        print_info("Starting auto-restart daemon...")
        print_warning("Daemon akan berjalan di background. Tekan Ctrl+C untuk stop.")
        subprocess.run(["python3", str(Path(__file__).parent / "youtube_live.py"), "auto-restart-daemon"])
    
    input("\n  Tekan Enter untuk lanjut...")


def menu_tools():
    """Tools and utilities menu."""
    clear_screen()
    print_header("🛠️ TOOLS & UTILITIES")
    
    print_section("Available Tools")
    print("  1. Check Dependencies")
    print("  2. View All Logs")
    print("  3. Clear Old Logs")
    print("  4. Test FFmpeg")
    print("  5. System Info")
    print("  0. Kembali")
    
    choice = input(f"\n{Colors.YELLOW}Pilihan: {Colors.RESET}").strip()
    
    if choice == "1":
        print_section("Checking Dependencies")
        if check_dependencies():
            print_success("All dependencies installed!")
        else:
            print_error("Some dependencies missing!")
    
    elif choice == "2":
        if LOG_DIR.exists():
            logs = sorted(LOG_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
            if logs:
                print(f"\n  Latest log: {logs[0]}")
                subprocess.run(f"tail -50 {logs[0]}", shell=True)
            else:
                print_warning("No logs found!")
        else:
            print_warning("Log directory not found!")
    
    elif choice == "3":
        confirm = input("  Clear all logs? (y/n): ").strip().lower()
        if confirm == "y" and LOG_DIR.exists():
            for log in LOG_DIR.glob("*.log"):
                log.unlink()
            print_success("All logs cleared!")
    
    elif choice == "4":
        print_section("Testing FFmpeg")
        subprocess.run("ffmpeg -version | head -3", shell=True)
    
    elif choice == "5":
        print_section("System Info")
        subprocess.run("uname -a", shell=True)
        subprocess.run("df -h /", shell=True)
        subprocess.run("free -h", shell=True)
    
    input("\n  Tekan Enter untuk lanjut...")


def main_menu():
    """Main menu loop."""
    while True:
        clear_screen()
        print_header("🎥 YOUTUBE LIVE STREAMING MANAGER")
        
        config = load_config()
        session_name = config.get("session_name", "youtube_live")
        is_live = get_session_status(session_name)
        
        status = f"{Colors.GREEN}🟢 LIVE{Colors.RESET}" if is_live else f"{Colors.RED}⚫ OFFLINE{Colors.RESET}"
        
        print(f"  Main Session : {session_name}")
        print(f"  Status       : {status}")
        print(f"  Video        : {config.get('video_path', '/root/live.mp4')}")
        
        print_section("Main Menu")
        print("  1. 📋 Setup Configuration")
        print("  2. 🔴 Start Single Stream")
        print("  3. 📡 Multi-Streaming")
        print("  4. ⏰ Auto-Restart")
        print("  5. 📊 Status")
        print("  6. 🔍 Monitor")
        print("  7. ⏹️ Stop Streaming")
        print("  8. 📥 Download (Google Drive)")
        print("  9. 🛠️ Tools")
        print("  0. Exit")
        
        choice = input(f"\n{Colors.YELLOW}╭─ Pilihan: {Colors.RESET}").strip()

        if choice == "1":
            menu_setup()
        elif choice == "2":
            menu_single_stream()
        elif choice == "3":
            menu_multi_stream()
        elif choice == "4":
            menu_auto_restart()
        elif choice == "5":
            menu_status()
        elif choice == "6":
            menu_monitor()
        elif choice == "7":
            menu_stop()
        elif choice == "8":
            menu_download()
        elif choice == "9":
            menu_tools()
        elif choice == "0":
            print(f"\n{Colors.CYAN}Terima kasih! Happy Streaming! 🎥{Colors.RESET}\n")
            break


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}✓ Exit.{Colors.RESET}\n")
        sys.exit(0)
