#!/usr/bin/env python3
"""
YouTube Live Streaming - Auto-Restart Daemon
Daemon untuk auto-restart streaming dengan watchdog monitoring.
"""

import json
import os
import subprocess
import sys
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_FILE = Path.home() / ".youtube_live_config.json"
MULTI_CONFIG_FILE = Path.home() / ".youtube_live_multi_config.json"
AUTO_RESTART_FILE = Path.home() / ".youtube_live_auto_restart.json"
WATCHDOG_FILE = Path.home() / ".youtube_live_watchdog.json"
LOG_DIR = Path("/var/log/youtube_live")
PID_FILE = Path("/var/run/youtube_live_daemon.pid")
DEFAULT_VIDEO_PATH = "/root/live.mp4"
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"

RESTART_DELAY = 5
MAX_RESTART_ATTEMPTS = 3
WATCHDOG_CHECK_INTERVAL = 30


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log_message(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "auto_restart_daemon.log"
    with open(log_file, "a") as f:
        f.write(log_line + "\n")


def load_json_file(filepath: Path, default: dict) -> dict:
    if filepath.exists():
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default


def save_json_file(filepath: Path, data: dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def get_session_status(session_name: str) -> bool:
    try:
        result = subprocess.run(
            f"tmux list-sessions 2>/dev/null | grep -E '^{session_name}:'",
            shell=True, capture_output=True, text=True
        )
        return result.stdout.strip() != ""
    except Exception as e:
        log_message(f"Error checking session {session_name}: {e}", "ERROR")
        return False


def stop_session(session_name: str) -> bool:
    try:
        if not get_session_status(session_name):
            return True
        log_message(f"Stopping session: {session_name}")
        subprocess.run(f"tmux send-keys -t {session_name} C-c", shell=True)
        time.sleep(2)
        if get_session_status(session_name):
            subprocess.run(f"tmux kill-session -t {session_name}", shell=True)
            time.sleep(1)
        if not get_session_status(session_name):
            log_message(f"Session {session_name} stopped successfully")
            return True
        log_message(f"Failed to stop session {session_name}", "ERROR")
        return False
    except Exception as e:
        log_message(f"Error stopping session {session_name}: {e}", "ERROR")
        return False


def start_single_stream(session_name=None, video_path=None, duration=None) -> bool:
    config = load_json_file(CONFIG_FILE, {})
    session_name = session_name or config.get("session_name", "youtube_live")
    video_path = video_path or config.get("video_path", DEFAULT_VIDEO_PATH)
    stream_key = config.get("stream_key", "")
    
    if not stream_key:
        log_message("Stream key not configured", "ERROR")
        return False
    if not Path(video_path).exists():
        log_message(f"Video file not found: {video_path}", "ERROR")
        return False
    if get_session_status(session_name):
        stop_session(session_name)
        time.sleep(RESTART_DELAY)
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{session_name}_{timestamp}.log"
    
    ffmpeg_cmd = ["ffmpeg", "-stream_loop", "-1", "-re", "-i", video_path,
                  "-f", "flv", "-c:v", "copy", "-c:a", "copy",
                  f"{RTMP_URL}/{stream_key}"]
    if duration:
        ffmpeg_cmd = ["timeout", f"{duration}h"] + ffmpeg_cmd
    
    cmd_str = " ".join(ffmpeg_cmd)
    tmux_cmd = f"tmux new -d -s {session_name} '{cmd_str} 2>&1 | tee {log_file}'"
    
    try:
        result = subprocess.run(tmux_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            time.sleep(2)
            if get_session_status(session_name):
                log_message(f"Started session: {session_name}")
                return True
        log_message(f"Failed to start session: {session_name}", "ERROR")
        return False
    except Exception as e:
        log_message(f"Error starting session: {e}", "ERROR")
        return False


def start_multi_stream(session_name: str, stream_key: str, rtmp_url: str,
                       video_path=None) -> bool:
    video_path = video_path or DEFAULT_VIDEO_PATH
    if not Path(video_path).exists():
        log_message(f"Video file not found: {video_path}", "ERROR")
        return False
    if get_session_status(session_name):
        stop_session(session_name)
        time.sleep(RESTART_DELAY)
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{session_name}_{timestamp}.log"
    
    cmd = f"ffmpeg -stream_loop -1 -re -i {video_path} -f flv -c:v copy -c:a copy {rtmp_url}/{stream_key} 2>&1 | tee {log_file}"
    tmux_cmd = f"tmux new -d -s {session_name} '{cmd}'"
    
    try:
        result = subprocess.run(tmux_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            time.sleep(2)
            if get_session_status(session_name):
                log_message(f"Started multi-stream: {session_name}")
                return True
        log_message(f"Failed to start multi-stream: {session_name}", "ERROR")
        return False
    except Exception as e:
        log_message(f"Error starting multi-stream: {e}", "ERROR")
        return False


def restart_all_streams() -> Dict[str, bool]:
    results = {}
    config = load_json_file(CONFIG_FILE, {})
    log_message("=" * 50)
    log_message("Starting auto-restart for all streams")
    log_message("=" * 50)
    
    session_name = config.get("session_name", "youtube_live")
    if get_session_status(session_name):
        log_message(f"Restarting single stream: {session_name}")
        results[session_name] = start_single_stream()
    else:
        results[session_name] = None
    
    multi_config = load_json_file(MULTI_CONFIG_FILE, {})
    for stream in multi_config.get("streams", []):
        sess = stream.get("session_name", "")
        stream_key = stream.get("stream_key", "")
        rtmp_url = stream.get("rtmp_url", "")
        platform = stream.get("platform", "unknown")
        
        if sess and stream_key and rtmp_url:
            if get_session_status(sess):
                log_message(f"Restarting {platform} stream: {sess}")
                results[sess] = start_multi_stream(sess, stream_key, rtmp_url)
            else:
                results[sess] = None
    
    success = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    log_message(f"Restart complete: {success} success, {failed} failed, {skipped} skipped")
    return results


def check_stream_health(session_name: str) -> bool:
    try:
        if not get_session_status(session_name):
            return False
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logs = sorted(LOG_DIR.glob(f"{session_name}_*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        if logs:
            latest_log = logs[0]
            mtime = datetime.fromtimestamp(latest_log.stat().st_mtime)
            elapsed = (datetime.now() - mtime).total_seconds()
            if elapsed > 120:
                return False
        return True
    except Exception as e:
        log_message(f"Error checking stream health: {e}", "ERROR")
        return False


class AutoRestartDaemon:
    def __init__(self):
        self.running = True
        self.config = load_json_file(AUTO_RESTART_FILE, {"enabled": False, "interval_hours": 6})
        self.restart_attempts = {}
        self.last_restart = {}
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        log_message(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def write_pid(self):
        try:
            PID_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PID_FILE, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            log_message(f"Error writing PID file: {e}", "ERROR")
    
    def remove_pid(self):
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
        except Exception as e:
            log_message(f"Error removing PID file: {e}", "ERROR")
    
    def should_restart(self) -> bool:
        interval_seconds = self.config.get("interval_hours", 6) * 3600
        for session_name, last_restart in self.last_restart.items():
            try:
                last_dt = datetime.fromisoformat(last_restart)
                elapsed = (datetime.now() - last_dt).total_seconds()
                if elapsed >= interval_seconds:
                    return True
            except Exception:
                pass
        return False
    
    def check_and_restart_unhealthy(self):
        active_sessions = []
        config = load_json_file(CONFIG_FILE, {})
        single_session = config.get("session_name", "youtube_live")
        if get_session_status(single_session):
            active_sessions.append(single_session)
        
        multi_config = load_json_file(MULTI_CONFIG_FILE, {})
        for stream in multi_config.get("streams", []):
            sess = stream.get("session_name", "")
            if sess and get_session_status(sess):
                active_sessions.append(sess)
        
        for session in active_sessions:
            health = check_stream_health(session)
            if not health:
                log_message(f"Stream {session} unhealthy, restarting...")
                attempts = self.restart_attempts.get(session, 0)
                if attempts >= MAX_RESTART_ATTEMPTS:
                    log_message(f"Max attempts for {session}", "ERROR")
                    continue
                self.restart_attempts[session] = attempts + 1
                if session == single_session:
                    start_single_stream()
                else:
                    for stream in multi_config.get("streams", []):
                        if stream.get("session_name") == session:
                            start_multi_stream(session, stream.get("stream_key", ""), stream.get("rtmp_url", ""))
                            break
                self.last_restart[session] = datetime.now().isoformat()
                time.sleep(RESTART_DELAY)
            else:
                self.restart_attempts[session] = 0
    
    def run(self):
        log_message("=" * 60)
        log_message("Auto-Restart Daemon Started")
        log_message(f"Interval: {self.config.get('interval_hours', 6)} hours")
        log_message("=" * 60)
        self.write_pid()
        
        config = load_json_file(CONFIG_FILE, {})
        single_session = config.get("session_name", "youtube_live")
        if get_session_status(single_session):
            self.last_restart[single_session] = datetime.now().isoformat()
        
        multi_config = load_json_file(MULTI_CONFIG_FILE, {})
        for stream in multi_config.get("streams", []):
            sess = stream.get("session_name", "")
            if sess and get_session_status(sess):
                self.last_restart[sess] = datetime.now().isoformat()
        
        check_count = 0
        try:
            while self.running:
                check_count += 1
                time.sleep(WATCHDOG_CHECK_INTERVAL)
                self.check_and_restart_unhealthy()
                if self.should_restart():
                    log_message("Interval reached, triggering restart...")
                    restart_all_streams()
                    for session in list(self.last_restart.keys()):
                        self.last_restart[session] = datetime.now().isoformat()
                    self.restart_attempts = {}
                if check_count % 10 == 0:
                    active_count = len([s for s in self.last_restart.keys() if get_session_status(s)])
                    log_message(f"Status: {active_count} active streams")
        except Exception as e:
            log_message(f"Daemon error: {e}", "ERROR")
        finally:
            self.remove_pid()
            log_message("Auto-Restart Daemon Stopped")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Live Auto-Restart Daemon")
    parser.add_argument("action", nargs="?", choices=["start", "stop", "status", "restart", "run"],
                       default="start", help="Action to perform")
    args = parser.parse_args()
    
    if args.action == "start":
        if PID_FILE.exists():
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                subprocess.run(f"kill -0 {pid}", shell=True, capture_output=True)
                print(f"Daemon already running (PID: {pid})")
                sys.exit(1)
            except Exception:
                PID_FILE.unlink()
        
        daemon_script = Path(__file__).absolute()
        tmux_cmd = f"tmux new -d -s youtube_auto_restart 'python3 {daemon_script} run'"
        subprocess.run(tmux_cmd, shell=True)
        print("Daemon started in tmux session 'youtube_auto_restart'")
        print("  Logs: tail -f /var/log/youtube_live/auto_restart_daemon.log")
        print("  Attach: tmux attach -t youtube_auto_restart")
    
    elif args.action == "run":
        daemon = AutoRestartDaemon()
        daemon.run()
    
    elif args.action == "stop":
        if PID_FILE.exists():
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                subprocess.run(f"kill {pid}", shell=True)
                print("Daemon stopped")
            except Exception as e:
                print(f"Error: {e}")
        subprocess.run("tmux kill-session -t youtube_auto_restart 2>/dev/null", shell=True)
        if PID_FILE.exists():
            PID_FILE.unlink()
    
    elif args.action == "status":
        running = False
        if PID_FILE.exists():
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                subprocess.run(f"kill -0 {pid}", shell=True, capture_output=True)
                print(f"Daemon running (PID: {pid})")
                running = True
            except Exception:
                print("PID file exists but process not running")
        
        result = subprocess.run("tmux list-sessions 2>/dev/null | grep youtube_auto_restart",
                               shell=True, capture_output=True, text=True)
        if result.stdout and not running:
            print("Daemon running in tmux")
            running = True
        
        if not running:
            print("Daemon not running")
        
        config = load_json_file(AUTO_RESTART_FILE, {})
        print(f"\nConfig: enabled={config.get('enabled', False)}, interval={config.get('interval_hours', 6)}h")
    
    elif args.action == "restart":
        subprocess.run("tmux kill-session -t youtube_auto_restart 2>/dev/null", shell=True)
        if PID_FILE.exists():
            PID_FILE.unlink()
        time.sleep(1)
        daemon_script = Path(__file__).absolute()
        tmux_cmd = f"tmux new -d -s youtube_auto_restart 'python3 {daemon_script} run'"
        subprocess.run(tmux_cmd, shell=True)
        print("Daemon restarted")


if __name__ == "__main__":
    main()
