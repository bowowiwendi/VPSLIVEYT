#!/usr/bin/env python3
"""
YouTube Live Streaming - Shared Utilities
Common functions used across all modules.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Default paths
DEFAULT_CONFIG_FILE = Path.home() / ".youtube_live_config.json"
DEFAULT_MULTI_CONFIG_FILE = Path.home() / ".youtube_live_multi_config.json"
DEFAULT_AUTO_RESTART_FILE = Path.home() / ".youtube_live_auto_restart.json"
DEFAULT_WATCHDOG_FILE = Path.home() / ".youtube_live_watchdog.json"
DEFAULT_LOG_DIR = Path("/var/log/youtube_live")
DEFAULT_VIDEO_PATH = "/root/live.mp4"
DEFAULT_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"

# RTMP URLs for various platforms
RTMP_PLATFORMS = {
    "youtube": "rtmp://a.rtmp.youtube.com/live2",
    "youtube_secondary": "rtmp://b.rtmp.youtube.com/live2",
    "facebook": "rtmps://live-api-s.facebook.com:443/rtmp",
    "twitch": "rtmp://live.twitch.tv/app",
    "tiktok": "rtmp://push.tiktok.com/live",
    "custom": ""
}


class Colors:
    """ANSI color codes for terminal output."""
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


# ==================== Configuration Functions ====================

def load_json_file(filepath: Path, default: Any = None) -> Any:
    """Load JSON file with default value on error."""
    if default is None:
        default = {}
    if filepath.exists():
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def save_json_file(filepath: Path, data: Any) -> bool:
    """Save JSON file with error handling."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except (IOError, OSError) as e:
        print(f"Error saving {filepath}: {e}")
        return False


def load_config(config_file: Path = None) -> Dict:
    """Load main configuration."""
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE
    default = {
        "stream_key": "",
        "video_path": DEFAULT_VIDEO_PATH,
        "session_name": "youtube_live",
        "videos": []  # Support for multiple videos
    }
    return load_json_file(config_file, default)


def save_config(config: Dict, config_file: Path = None) -> bool:
    """Save main configuration."""
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE
    return save_json_file(config_file, config)


def load_multi_config(config_file: Path = None) -> Dict:
    """Load multi-stream configuration."""
    if config_file is None:
        config_file = DEFAULT_MULTI_CONFIG_FILE
    default = {"streams": []}
    return load_json_file(config_file, default)


def save_multi_config(config: Dict, config_file: Path = None) -> bool:
    """Save multi-stream configuration."""
    if config_file is None:
        config_file = DEFAULT_MULTI_CONFIG_FILE
    return save_json_file(config_file, config)


def load_auto_restart_config(config_file: Path = None) -> Dict:
    """Load auto-restart configuration."""
    if config_file is None:
        config_file = DEFAULT_AUTO_RESTART_FILE
    default = {"enabled": False, "interval_hours": 6, "sessions": []}
    return load_json_file(config_file, default)


def save_auto_restart_config(config: Dict, config_file: Path = None) -> bool:
    """Save auto-restart configuration."""
    if config_file is None:
        config_file = DEFAULT_AUTO_RESTART_FILE
    return save_json_file(config_file, config)


# ==================== TMux Session Functions ====================

def get_session_status(session_name: str) -> bool:
    """Check if tmux session is active."""
    try:
        result = subprocess.run(
            f"tmux list-sessions 2>/dev/null | grep -E '^{session_name}:'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() != ""
    except (subprocess.TimeoutExpired, Exception):
        return False


def get_all_sessions() -> List[str]:
    """Get all active tmux sessions."""
    try:
        result = subprocess.run(
            "tmux list-sessions 2>/dev/null",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        sessions = []
        for line in result.stdout.strip().split("\n"):
            if line:
                sessions.append(line.split(":")[0])
        return sessions
    except Exception:
        return []


def stop_session(session_name: str, timeout: int = 10) -> bool:
    """Stop tmux session with graceful shutdown."""
    try:
        if not get_session_status(session_name):
            return True
        
        # Try graceful shutdown with Ctrl+C
        subprocess.run(f"tmux send-keys -t {session_name} C-c", shell=True, timeout=5)
        time.sleep(2)
        
        # Force kill if still running
        if get_session_status(session_name):
            subprocess.run(f"tmux kill-session -t {session_name}", shell=True, timeout=5)
            time.sleep(1)
        
        return not get_session_status(session_name)
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"Error stopping session {session_name}: {e}")
        return False


def start_session_command(session_name: str, command: str, log_file: Path = None) -> bool:
    """Start a tmux session with given command."""
    try:
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            tmux_cmd = f"tmux new -d -s {session_name} '{command} 2>&1 | tee {log_file}'"
        else:
            tmux_cmd = f"tmux new -d -s {session_name} '{command}'"
        
        result = subprocess.run(tmux_cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            time.sleep(2)  # Wait for session to start
            return get_session_status(session_name)
        return False
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"Error starting session {session_name}: {e}")
        return False


# ==================== FFmpeg Functions ====================

def build_ffmpeg_command(video_path: str, rtmp_url: str, stream_key: str, 
                         duration: float = None, copy_codec: bool = True) -> List[str]:
    """Build FFmpeg command for streaming."""
    cmd = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-re",
        "-i", video_path
    ]
    
    if copy_codec:
        cmd.extend(["-f", "flv", "-c:v", "copy", "-c:a", "copy"])
    else:
        cmd.extend([
            "-f", "flv",
            "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
            "-c:a", "aac", "-b:a", "128k"
        ])
    
    cmd.append(f"{rtmp_url}/{stream_key}")
    
    if duration:
        cmd = ["timeout", f"{duration}h"] + cmd
    
    return cmd


def get_ffmpeg_command_str(video_path: str, rtmp_url: str, stream_key: str,
                           duration: float = None, copy_codec: bool = True) -> str:
    """Get FFmpeg command as string."""
    cmd = build_ffmpeg_command(video_path, rtmp_url, stream_key, duration, copy_codec)
    return " ".join(cmd)


# ==================== Logging Functions ====================

def ensure_log_dir(log_dir: Path = None) -> Path:
    """Ensure log directory exists."""
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_file(session_name: str, log_dir: Path = None) -> Path:
    """Get log file path for a session."""
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"{session_name}_{timestamp}.log"


def get_recent_logs(session_name: str = None, limit: int = 5, log_dir: Path = None) -> List[Path]:
    """Get recent log files."""
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    if not log_dir.exists():
        return []
    
    if session_name:
        logs = sorted(
            log_dir.glob(f"{session_name}_*.log"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
    else:
        logs = sorted(
            log_dir.glob("*.log"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
    
    return logs[:limit]


def read_log_tail(log_file: Path, lines: int = 10) -> List[str]:
    """Read last N lines from log file."""
    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception:
        return []


# ==================== System Functions ====================

def check_dependencies(deps: Dict[str, str] = None) -> tuple:
    """
    Check if dependencies are installed.
    Returns (all_installed, missing_list)
    """
    if deps is None:
        deps = {
            "ffmpeg": "ffmpeg -version",
            "tmux": "tmux -V",
            "python3": "python3 --version"
        }
    
    missing = []
    for name, cmd in deps.items():
        try:
            result = subprocess.run(
                cmd, shell=True, check=True, capture_output=True, timeout=10
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            missing.append(name)
    
    return (len(missing) == 0, missing)


def get_system_stats() -> Dict:
    """Get system statistics (CPU, Memory, Disk)."""
    stats = {"cpu": 0, "memory": "N/A", "disk": "N/A"}
    
    try:
        # CPU
        result = subprocess.run(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            stats["cpu"] = float(result.stdout.strip())
    except Exception:
        pass
    
    try:
        # Memory
        result = subprocess.run(
            "free -m | awk 'NR==2{printf \"%.1f/%.1f MB (%.1f%%)\", $3,$2,$3*100/$2}'",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            stats["memory"] = result.stdout.strip()
    except Exception:
        pass
    
    try:
        # Disk
        result = subprocess.run(
            "df -h / | awk 'NR==2{printf \"%s/%s (%s)\", $3,$2,$5}'",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            stats["disk"] = result.stdout.strip()
    except Exception:
        pass
    
    return stats


def get_ffmpeg_process_count() -> int:
    """Get count of active FFmpeg processes."""
    try:
        result = subprocess.run(
            "pgrep -c ffmpeg",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            return int(result.stdout.strip())
    except Exception:
        pass
    return 0


# ==================== Print Helper Functions ====================

def print_header(title: str):
    """Print formatted header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}\n")


def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}┌─ {title} {'─' * (50 - len(title))}{Colors.RESET}")


def print_success(msg: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg: str):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")


# ==================== Video Management Functions ====================

def get_video_list(config: Dict = None) -> List[Dict]:
    """Get list of videos from config."""
    if config is None:
        config = load_config()
    
    videos = config.get("videos", [])
    
    # Also include legacy video_path
    if config.get("video_path") and not any(v.get("path") == config["video_path"] for v in videos):
        videos.append({
            "name": "Default Video",
            "path": config["video_path"],
            "is_default": True
        })
    
    return videos


def validate_video_path(path: str) -> bool:
    """Validate video file exists and is readable."""
    try:
        video_path = Path(path)
        if not video_path.exists():
            return False
        if not video_path.is_file():
            return False
        # Check if file is readable
        with open(video_path, "rb") as f:
            f.read(1024)
        return True
    except Exception:
        return False


def get_video_duration(path: str) -> Optional[float]:
    """Get video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def scan_video_directory(directory: str = "/root") -> List[Dict]:
    """Scan directory for video files."""
    video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm"]
    videos = []
    
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return videos
        
        for ext in video_extensions:
            for video_file in dir_path.glob(f"*{ext}"):
                duration = get_video_duration(str(video_file))
                videos.append({
                    "name": video_file.stem,
                    "path": str(video_file),
                    "duration": duration,
                    "size": video_file.stat().st_size
                })
    except Exception:
        pass
    
    return videos


# Import time for functions that need it
import time

