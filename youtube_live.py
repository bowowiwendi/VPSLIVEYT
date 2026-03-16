#!/usr/bin/env python3
"""
YouTube Live Streaming Manager
Mengelola live streaming ke YouTube dengan FFmpeg, tmux, dan monitoring.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path.home() / ".youtube_live_config.json"
AUTO_RESTART_FILE = Path.home() / ".youtube_live_auto_restart.json"
LOG_DIR = Path("/var/log/youtube_live")
DEFAULT_VIDEO_PATH = "/root/live.mp4"
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"


def load_config():
    """Load konfigurasi dari file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stream_key": "", "video_path": DEFAULT_VIDEO_PATH, "session_name": "youtube_live"}


def save_config(config):
    """Simpan konfigurasi ke file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✓ Konfigurasi disimpan ke {CONFIG_FILE}")


def load_auto_restart_config():
    """Load auto-restart konfigurasi."""
    if AUTO_RESTART_FILE.exists():
        with open(AUTO_RESTART_FILE, "r") as f:
            return json.load(f)
    return {"enabled": False, "interval_hours": 6, "sessions": []}


def save_auto_restart_config(config):
    """Simpan auto-restart konfigurasi."""
    AUTO_RESTART_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTO_RESTART_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✓ Auto-restart konfigurasi disimpan")


class Colors:
    """ANSI color codes."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_header(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")


def setup_config(stream_key=None, video_path=None, session_name=None):
    """Setup atau update konfigurasi."""
    config = load_config()
    
    if stream_key:
        config["stream_key"] = stream_key
    if video_path:
        config["video_path"] = video_path
    if session_name:
        config["session_name"] = session_name
    
    # Interactive setup jika tidak ada stream_key
    if not config.get("stream_key"):
        stream_key = input("Masukkan YouTube Stream Key: ").strip()
        if stream_key:
            config["stream_key"] = stream_key
    
    save_config(config)
    return config


def check_dependencies():
    """Cek apakah semua dependencies terinstall."""
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
        print(f"✗ Dependencies missing: {', '.join(missing)}")
        print("  Jalankan: sudo apt update && sudo apt install -y ffmpeg tmux python3 python3-pip")
        print("  Lalu: pip install gdown")
        return False
    return True


def get_session_status(session_name):
    """Dapatkan status sesi tmux."""
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


def start_stream(video_path=None, duration=None, session_name=None):
    """Mulai live streaming."""
    config = load_config()
    
    video_path = video_path or config.get("video_path", DEFAULT_VIDEO_PATH)
    session_name = session_name or config.get("session_name", "youtube_live")
    stream_key = config.get("stream_key")
    
    if not stream_key:
        print("✗ Stream Key belum diatur!")
        print("  Jalankan: python3 youtube_live.py setup")
        return False
    
    if not Path(video_path).exists():
        print(f"✗ Video file tidak ditemukan: {video_path}")
        return False
    
    # Cek apakah sesi sudah berjalan
    if get_session_status(session_name):
        print(f"⚠ Sesi '{session_name}' sudah berjalan. Stop dulu atau gunakan nama lain.")
        return False
    
    # Buat log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Build FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-re",
        "-i", video_path,
        "-f", "flv",
        "-c:v", "copy",
        "-c:a", "copy",
        f"{RTMP_URL}/{stream_key}"
    ]
    
    # Tambahkan timeout jika duration ditentukan
    if duration:
        ffmpeg_cmd = ["timeout", f"{duration}h"] + ffmpeg_cmd
    
    cmd_str = " ".join(ffmpeg_cmd)
    
    # Start tmux session
    print(f"✓ Memulai live streaming...")
    print(f"  Video: {video_path}")
    print(f"  Session: {session_name}")
    if duration:
        print(f"  Duration: {duration} jam")
    print(f"  Log: {log_file}")
    
    # Create tmux session dengan command
    tmux_cmd = f"tmux new -d -s {session_name} '{cmd_str} 2>&1 | tee {log_file}'"
    
    try:
        subprocess.run(tmux_cmd, shell=True, check=True)
        print(f"✓ Live streaming dimulai!")
        print(f"  Untuk monitor: python3 youtube_live.py status")
        print(f"  Untuk lihat log: tail -f {log_file}")
        print(f"  Untuk stop: python3 youtube_live.py stop")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Gagal memulai streaming: {e}")
        return False


def stop_stream(session_name=None):
    """Stop live streaming."""
    config = load_config()
    session_name = session_name or config.get("session_name", "youtube_live")
    
    if not get_session_status(session_name):
        print(f"✗ Sesi '{session_name}' tidak ditemukan.")
        return False
    
    try:
        subprocess.run(f"tmux kill-session -t {session_name}", shell=True, check=True)
        print(f"✓ Live streaming dihentikan.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Gagal stop streaming: {e}")
        return False


def status():
    """Tampilkan status live streaming."""
    config = load_config()
    session_name = config.get("session_name", "youtube_live")
    
    print("\n" + "=" * 50)
    print("📺 YOUTUBE LIVE STREAMING STATUS")
    print("=" * 50)
    
    # Config status
    print(f"\n📁 Konfigurasi:")
    print(f"   Config file: {CONFIG_FILE}")
    print(f"   Stream Key: {'✓ Tersetel' if config.get('stream_key') else '✗ Belum disetel'}")
    print(f"   Video Path: {config.get('video_path', DEFAULT_VIDEO_PATH)}")
    print(f"   Session Name: {session_name}")
    
    # Session status
    print(f"\n🔴 Status Streaming:")
    is_running = get_session_status(session_name)
    if is_running:
        print(f"   Status: 🟢 LIVE")
        print(f"   Session: {session_name}")
        
        # Get tmux session info
        try:
            result = subprocess.run(
                f"tmux list-sessions | grep -E '^{session_name}:'",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(f"   Info: {result.stdout.strip()}")
        except Exception:
            pass
    else:
        print(f"   Status: ⚫ OFFLINE")
    
    # Recent logs
    print(f"\n📋 Log Terbaru:")
    if LOG_DIR.exists():
        logs = sorted(LOG_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        if logs:
            latest_log = logs[0]
            print(f"   File: {latest_log}")
            print(f"   Ukuran: {latest_log.stat().st_size} bytes")
            # Tampilkan 5 baris terakhir
            try:
                with open(latest_log, "r") as f:
                    lines = f.readlines()[-5:]
                    if lines:
                        print("   Preview:")
                        for line in lines:
                            print(f"     {line.strip()}")
            except Exception:
                pass
        else:
            print("   Belum ada log")
    else:
        print("   Log directory belum ada")
    
    print("\n" + "=" * 50)
    print("Commands:")
    print("  start   - Mulai streaming")
    print("  stop    - Stop streaming")
    print("  setup   - Setup konfigurasi")
    print("  monitor - Monitor real-time")
    print("=" * 50 + "\n")


def monitor(session_name=None):
    """Monitor live streaming secara real-time."""
    config = load_config()
    session_name = session_name or config.get("session_name", "youtube_live")
    
    print(f"🔍 Monitoring sesi: {session_name}")
    print("Tekan Ctrl+C untuk keluar\n")
    
    try:
        while True:
            is_running = get_session_status(session_name)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if is_running:
                status_icon = "🟢 LIVE"
            else:
                status_icon = "⚫ OFFLINE"
            
            print(f"[{timestamp}] {status_icon}", end="\r")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring dihentikan.")


def download_video(url, output_path=None):
    """Download video dari Google Drive menggunakan gdown."""
    print(f"📥 Downloading dari: {url}")
    
    try:
        cmd = ["gdown", url]
        if output_path:
            cmd.extend(["-O", output_path])
        
        subprocess.run(cmd, check=True)
        print("✓ Download selesai!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Download gagal: {e}")
        return False


def list_sessions():
    """List semua tmux sessions yang terkait dengan streaming."""
    try:
        result = subprocess.run(
            "tmux list-sessions 2>/dev/null",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.stdout:
            print("\n📺 Active TMUX Sessions:")
            print("-" * 40)
            for line in result.stdout.strip().split("\n"):
                print(f"  {line}")
            print("-" * 40)
        else:
            print("Tidak ada sesi tmux aktif.")
    except Exception as e:
        print(f"Error: {e}")


# ==================== DUAL STREAM SUPPORT ====================

def start_dual_stream(video_path_1=None, stream_key_1=None, session_name_1=None,
                      video_path_2=None, stream_key_2=None, session_name_2=None,
                      rtmp_url=None):
    """
    Start 2 simultaneous streams with different videos.
    Each stream runs independently with its own video and stream key.
    """
    config = load_config()
    rtmp_url = rtmp_url or RTMP_URL

    # Stream 1 configuration
    video_path_1 = video_path_1 or config.get("video_path", DEFAULT_VIDEO_PATH)
    stream_key_1 = stream_key_1 or config.get("stream_key")
    session_name_1 = session_name_1 or config.get("session_name", "youtube_live") + "_1"

    # Stream 2 configuration  
    video_path_2 = video_path_2 or config.get("video_path", DEFAULT_VIDEO_PATH)
    stream_key_2 = stream_key_2 or config.get("stream_key")
    session_name_2 = session_name_2 or config.get("session_name", "youtube_live") + "_2"

    # Validate configurations
    if not stream_key_1 or not stream_key_2:
        print_error("Both stream keys must be provided!")
        return False

    if not Path(video_path_1).exists():
        print_error(f"Video 1 not found: {video_path_1}")
        return False

    if not Path(video_path_2).exists():
        print_error(f"Video 2 not found: {video_path_2}")
        return False

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    streams_started = 0

    # Start Stream 1
    if not get_session_status(session_name_1):
        log_file_1 = LOG_DIR / f"{session_name_1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        cmd_1 = f"ffmpeg -stream_loop -1 -re -i {video_path_1} -f flv -c:v copy -c:a copy {rtmp_url}/{stream_key_1} 2>&1 | tee {log_file_1}"
        tmux_cmd_1 = f"tmux new -d -s {session_name_1} '{cmd_1}'"

        try:
            subprocess.run(tmux_cmd_1, shell=True, check=True)
            time.sleep(2)
            if get_session_status(session_name_1):
                print_success(f"Stream 1 started: {session_name_1} (Video: {video_path_1})")
                streams_started += 1
            else:
                print_error(f"Stream 1 failed to start: {session_name_1}")
        except subprocess.CalledProcessError as e:
            print_error(f"Stream 1 error: {e}")
    else:
        print_warning(f"Stream 1 already running: {session_name_1}")

    # Start Stream 2
    if not get_session_status(session_name_2):
        log_file_2 = LOG_DIR / f"{session_name_2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        cmd_2 = f"ffmpeg -stream_loop -1 -re -i {video_path_2} -f flv -c:v copy -c:a copy {rtmp_url}/{stream_key_2} 2>&1 | tee {log_file_2}"
        tmux_cmd_2 = f"tmux new -d -s {session_name_2} '{cmd_2}'"

        try:
            subprocess.run(tmux_cmd_2, shell=True, check=True)
            time.sleep(2)
            if get_session_status(session_name_2):
                print_success(f"Stream 2 started: {session_name_2} (Video: {video_path_2})")
                streams_started += 1
            else:
                print_error(f"Stream 2 failed to start: {session_name_2}")
        except subprocess.CalledProcessError as e:
            print_error(f"Stream 2 error: {e}")
    else:
        print_warning(f"Stream 2 already running: {session_name_2}")

    print(f"\n✓ {streams_started}/2 streams started")
    if streams_started > 0:
        print(f"  Monitor: python3 youtube_live.py status")
        print(f"  Stop both: python3 youtube_live.py dual-stream-stop")

    return streams_started > 0


def stop_dual_stream(session_name_1=None, session_name_2=None):
    """Stop both dual streams."""
    config = load_config()
    session_name_1 = session_name_1 or config.get("session_name", "youtube_live") + "_1"
    session_name_2 = session_name_2 or config.get("session_name", "youtube_live") + "_2"

    stopped = 0

    if get_session_status(session_name_1):
        stop_session(session_name_1)
        print_success(f"Stream 1 stopped: {session_name_1}")
        stopped += 1
    else:
        print_warning(f"Stream 1 not running: {session_name_1}")

    if get_session_status(session_name_2):
        stop_session(session_name_2)
        print_success(f"Stream 2 stopped: {session_name_2}")
        stopped += 1
    else:
        print_warning(f"Stream 2 not running: {session_name_2}")

    print(f"\n✓ {stopped}/2 streams stopped")
    return stopped


def get_dual_stream_status():
    """Get status of dual streams."""
    config = load_config()
    session_name_1 = config.get("session_name", "youtube_live") + "_1"
    session_name_2 = config.get("session_name", "youtube_live") + "_2"

    status_1 = get_session_status(session_name_1)
    status_2 = get_session_status(session_name_2)

    return {
        "stream_1": {"session": session_name_1, "active": status_1},
        "stream_2": {"session": session_name_2, "active": status_2},
        "both_active": status_1 and status_2
    }


def start_multi_stream(video_path=None, duration=None):
    """Start multi-streaming ke berbagai platform."""
    config = load_config()
    multi_config_file = Path.home() / ".youtube_live_multi_config.json"
    
    video_path = video_path or config.get("video_path", DEFAULT_VIDEO_PATH)
    
    if not multi_config_file.exists():
        print("✗ Multi-stream config tidak ditemukan!")
        print("  Gunakan cli_menu.py untuk setup multi-stream")
        return False
    
    with open(multi_config_file, "r") as f:
        multi_config = json.load(f)
    
    streams = multi_config.get("streams", [])
    if not streams:
        print("✗ Tidak ada stream yang dikonfigurasi!")
        return False
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Memulai {len(streams)} multi-streams...")
    print(f"  Video: {video_path}")
    
    started = 0
    for stream in streams:
        session_name = stream.get("session_name", f"multi_{stream.get('platform', 'unknown')}")
        stream_key = stream.get("stream_key", "")
        rtmp_url = stream.get("rtmp_url", "")
        platform = stream.get("platform", "custom")
        
        if not stream_key or not rtmp_url:
            print(f"  ⚠ Skip {session_name}: Stream key atau RTMP URL kosong")
            continue
        
        if get_session_status(session_name):
            print(f"  ⚠ {session_name} sudah berjalan, skip...")
            continue
        
        log_file = LOG_DIR / f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-stream_loop", "-1",
            "-re",
            "-i", video_path,
            "-f", "flv",
            "-c:v", "copy",
            "-c:a", "copy",
            f"{rtmp_url}/{stream_key}"
        ]
        
        if duration:
            ffmpeg_cmd = ["timeout", f"{duration}h"] + ffmpeg_cmd
        
        cmd_str = " ".join(ffmpeg_cmd)
        
        tmux_cmd = f"tmux new -d -s {session_name} '{cmd_str} 2>&1 | tee {log_file}'"
        
        try:
            subprocess.run(tmux_cmd, shell=True, check=True)
            print(f"  ✓ Started: {session_name} ({platform})")
            started += 1
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed: {session_name} - {e}")
    
    print(f"\n✓ {started}/{len(streams)} streams dimulai!")
    print(f"  Monitor: python3 youtube_live.py status")
    print(f"  Stop all: python3 youtube_live.py multi-stop")
    return started > 0


def stop_multi_stream():
    """Stop semua multi-streams."""
    multi_config_file = Path.home() / ".youtube_live_multi_config.json"
    
    if not multi_config_file.exists():
        print("✗ Multi-stream config tidak ditemukan!")
        return False
    
    with open(multi_config_file, "r") as f:
        multi_config = json.load(f)
    
    streams = multi_config.get("streams", [])
    if not streams:
        print("✗ Tidak ada stream yang dikonfigurasi!")
        return False
    
    stopped = 0
    for stream in streams:
        session_name = stream.get("session_name", "")
        if session_name and get_session_status(session_name):
            try:
                subprocess.run(f"tmux kill-session -t {session_name}", shell=True, check=True)
                print(f"  ✓ Stopped: {session_name}")
                stopped += 1
            except subprocess.CalledProcessError:
                pass
    
    print(f"\n✓ {stopped} streams dihentikan!")
    return True


def enable_auto_restart(interval_hours=6, sessions=None):
    """Enable auto-restart untuk streaming."""
    config = load_auto_restart_config()
    config["enabled"] = True
    config["interval_hours"] = interval_hours
    if sessions:
        config["sessions"] = sessions
    save_auto_restart_config(config)
    print_success(f"✓ Auto-restart diaktifkan (interval: {interval_hours} jam)")


def disable_auto_restart():
    """Disable auto-restart."""
    config = load_auto_restart_config()
    config["enabled"] = False
    save_auto_restart_config(config)
    print_success("✓ Auto-restart dinonaktifkan")


def get_auto_restart_status():
    """Dapatkan status auto-restart."""
    config = load_auto_restart_config()
    return config


def auto_restart_stream(session_name=None, video_path=None, duration=None):
    """Restart sebuah stream."""
    config = load_config()
    
    session_name = session_name or config.get("session_name", "youtube_live")
    video_path = video_path or config.get("video_path", DEFAULT_VIDEO_PATH)
    
    # Stop existing session
    if get_session_status(session_name):
        subprocess.run(f"tmux kill-session -t {session_name}", shell=True)
        print(f"  ✓ Stopped: {session_name}")
    
    # Start new session
    stream_key = config.get("stream_key")
    if not stream_key:
        print_error("Stream Key belum disetel!")
        return False
    
    if not Path(video_path).exists():
        print_error(f"Video file tidak ditemukan: {video_path}")
        return False
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-re",
        "-i", video_path,
        "-f", "flv",
        "-c:v", "copy",
        "-c:a", "copy",
        f"{RTMP_URL}/{stream_key}"
    ]
    
    if duration:
        ffmpeg_cmd = ["timeout", f"{duration}h"] + ffmpeg_cmd
    
    cmd_str = " ".join(ffmpeg_cmd)
    tmux_cmd = f"tmux new -d -s {session_name} '{cmd_str} 2>&1 | tee {log_file}'"
    
    try:
        subprocess.run(tmux_cmd, shell=True, check=True)
        print_success(f"✓ Restarted: {session_name}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"✗ Failed restart: {session_name} - {e}")
        return False


def auto_restart_all_streams():
    """Auto-restart semua streams yang aktif."""
    multi_config_file = Path.home() / ".youtube_live_multi_config.json"
    
    print_info("Auto-restarting all streams...")
    
    # Restart single stream
    config = load_config()
    session_name = config.get("session_name", "youtube_live")
    if get_session_status(session_name):
        auto_restart_stream(session_name)
    
    # Restart multi-streams
    if multi_config_file.exists():
        with open(multi_config_file, "r") as f:
            multi_config = json.load(f)
        
        for stream in multi_config.get("streams", []):
            sess = stream.get("session_name", "")
            if sess and get_session_status(sess):
                # Stop
                subprocess.run(f"tmux kill-session -t {sess}", shell=True)
                
                # Start again
                video_path = config.get("video_path", DEFAULT_VIDEO_PATH)
                stream_key = stream.get("stream_key", "")
                rtmp_url = stream.get("rtmp_url", "")
                
                if stream_key and rtmp_url:
                    LOG_DIR.mkdir(parents=True, exist_ok=True)
                    log_file = LOG_DIR / f"{sess}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    
                    cmd = (
                        f"ffmpeg -stream_loop -1 -re -i {video_path} "
                        f"-f flv -c:v copy -c:a copy "
                        f"{rtmp_url}/{stream_key} "
                        f"2>&1 | tee {log_file}"
                    )
                    tmux_cmd = f"tmux new -d -s {sess} '{cmd}'"
                    subprocess.run(tmux_cmd, shell=True)
                    print_success(f"  Restarted: {sess}")
    
    print_success("Auto-restart complete!")


def run_auto_restart_daemon():
    """Jalankan daemon untuk auto-restart."""
    config = load_auto_restart_config()
    
    if not config.get("enabled", False):
        print_warning("Auto-restart tidak aktif")
        return
    
    interval = config.get("interval_hours", 6)
    interval_seconds = interval * 3600
    
    print_success(f"Auto-restart daemon started (interval: {interval} jam)")
    print_info(f"Next restart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        while True:
            time.sleep(interval_seconds)
            
            print_info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto-restart triggered!")
            auto_restart_all_streams()
            print_info(f"Next restart in {interval} hours...")
            
    except KeyboardInterrupt:
        print("\n✓ Auto-restart daemon stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Live Streaming Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 youtube_live.py setup              # Setup konfigurasi
  python3 youtube_live.py start              # Mulai streaming
  python3 youtube_live.py start -d 10        # Streaming 10 jam
  python3 youtube_live.py stop               # Stop streaming
  python3 youtube_live.py status             # Cek status
  python3 youtube_live.py monitor            # Monitor real-time
  python3 youtube_live.py download <URL>     # Download dari Google Drive
  python3 youtube_live.py multi-start        # Start multi-streaming
  python3 youtube_live.py multi-stop         # Stop semua multi-streams
  python3 youtube_live.py menu               # Interactive CLI menu
  python3 youtube_live.py auto-restart       # Setup auto-restart
  python3 youtube_live.py auto-restart-now   # Restart sekarang
        """
    )

    parser.add_argument("command", nargs="?", choices=[
        "setup", "start", "stop", "status", "monitor",
        "download", "list", "check", "multi-start",
        "multi-stop", "menu", "auto-restart", 
        "auto-restart-now", "auto-restart-daemon"
    ], help="Command untuk dijalankan")
    
    parser.add_argument("-k", "--stream-key", help="YouTube Stream Key")
    parser.add_argument("-v", "--video", help="Path ke video file")
    parser.add_argument("-n", "--name", help="Nama sesi tmux")
    parser.add_argument("-d", "--duration", type=float, help="Durasi streaming (jam)")
    parser.add_argument("-o", "--output", help="Output path untuk download")
    parser.add_argument("--url", help="URL Google Drive untuk download")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check dependencies untuk command tertentu
    if args.command in ["start", "stop", "status", "monitor", "list"]:
        if not check_dependencies():
            sys.exit(1)
    
    if args.command == "setup":
        config = {
            "stream_key": args.stream_key,
            "video_path": args.video or DEFAULT_VIDEO_PATH,
            "session_name": args.name or "youtube_live"
        }
        save_config(config)
    
    elif args.command == "start":
        start_stream(
            video_path=args.video,
            duration=args.duration,
            session_name=args.name
        )
    
    elif args.command == "stop":
        stop_stream(session_name=args.name)
    
    elif args.command == "status":
        status()
    
    elif args.command == "monitor":
        monitor(session_name=args.name)
    
    elif args.command == "download":
        url = args.url
        if not url and len(sys.argv) > 2:
            url = sys.argv[sys.argv.index("download") + 1]
        if url:
            download_video(url, args.output)
        else:
            print("✗ URL harus ditentukan!")
            print("  Contoh: python3 youtube_live.py download https://drive.google.com/uc?id=xxx")
    
    elif args.command == "list":
        list_sessions()
    
    elif args.command == "check":
        if check_dependencies():
            print("✓ Semua dependencies terinstall.")
        else:
            sys.exit(1)
    
    elif args.command == "multi-start":
        start_multi_stream(
            video_path=args.video,
            duration=args.duration
        )

    elif args.command == "multi-stop":
        stop_multi_stream()

    elif args.command == "menu":
        # Launch interactive CLI menu
        subprocess.run(["python3", str(Path(__file__).parent / "cli_menu.py")])

    elif args.command == "auto-restart":
        # Interactive auto-restart setup
        print_header("AUTO-RESTART SETUP")
        config = load_auto_restart_config()
        
        print(f"  Status      : {'✓ Enabled' if config.get('enabled') else '✗ Disabled'}")
        print(f"  Interval    : {config.get('interval_hours', 6)} jam")
        
        print("\n  Options:")
        print("  1. Enable auto-restart")
        print("  2. Disable auto-restart")
        print("  3. Set interval")
        print("  4. Restart now")
        
        choice = input("\n  Pilihan [1-4]: ").strip()

        if choice == "1":
            interval = input(f"  Interval (jam) [{config.get('interval_hours', 6)}]: ").strip()
            interval = int(interval) if interval.isdigit() else config.get('interval_hours', 6)
            enable_auto_restart(interval_hours=interval)
        elif choice == "2":
            disable_auto_restart()
        elif choice == "3":
            interval = input("  Interval (jam): ").strip()
            if interval.isdigit():
                enable_auto_restart(interval_hours=int(interval))
        elif choice == "4":
            auto_restart_all_streams()

    elif args.command == "auto-restart-now":
        auto_restart_all_streams()

    elif args.command == "auto-restart-daemon":
        # Use new daemon script
        daemon_script = Path(__file__).parent / "auto_restart_daemon.py"
        if len(sys.argv) > 2:
            action = sys.argv[2]
        else:
            action = "start"
        subprocess.run(["python3", str(daemon_script), action])

    elif args.command == "dual-stream":
        # Interactive dual stream setup
        print_header("DUAL STREAM SETUP")
        print("  Start 2 simultaneous streams with different videos")
        print()
        
        # Get configuration
        v1 = input("  Video 1 path [/root/live.mp4]: ").strip() or "/root/live.mp4"
        k1 = input("  Stream Key 1: ").strip()
        n1 = input("  Session Name 1 [youtube_live_1]: ").strip() or "youtube_live_1"
        
        v2 = input("  Video 2 path: ").strip()
        k2 = input("  Stream Key 2: ").strip()
        n2 = input("  Session Name 2 [youtube_live_2]: ").strip() or "youtube_live_2"
        
        if not k1 or not k2 or not v2:
            print_error("All fields required!")
        else:
            start_dual_stream(
                video_path_1=v1, stream_key_1=k1, session_name_1=n1,
                video_path_2=v2, stream_key_2=k2, session_name_2=n2
            )

    elif args.command == "dual-stream-stop":
        stop_dual_stream()

    elif args.command == "dual-stream-status":
        status = get_dual_stream_status()
        print_header("DUAL STREAM STATUS")
        s1 = status["stream_1"]
        s2 = status["stream_2"]
        print(f"  Stream 1 ({s1['session']}): {'🟢 LIVE' if s1['active'] else '⚫ OFFLINE'}")
        print(f"  Stream 2 ({s2['session']}): {'🟢 LIVE' if s2['active'] else '⚫ OFFLINE'}")
        print(f"  Both Active: {'✓ Yes' if status['both_active'] else '✗ No'}")


if __name__ == "__main__":
    main()
