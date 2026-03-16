#!/usr/bin/env python3
"""
YouTube Live Streaming - Web Dashboard
Mobile-friendly web interface for managing live streams.
"""

from flask import Flask, render_template_string, jsonify, request
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
from utils import *

app = Flask(__name__)

# ==================== HTML Templates ====================

def get_base_html(title="YouTube Live Manager", content="", page="home", extra_css="", extra_js=""):
    """Generate complete HTML page."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding-bottom: 80px;
        }}
        .header {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{ font-size: 1.3rem; color: #fff; }}
        .header .status {{ font-size: 0.85rem; opacity: 0.8; margin-top: 5px; }}
        .container {{ padding: 20px; max-width: 800px; margin: 0 auto; }}
        .card {{
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h2 {{ font-size: 1.1rem; margin-bottom: 15px; color: #4fc3f7; }}
        .card h3 {{ font-size: 1rem; margin: 15px 0 10px; color: #81d4fa; }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            border: none;
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.3s;
            margin: 5px;
        }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }}
        .btn-success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: #fff; }}
        .btn-danger {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: #fff; }}
        .btn-warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #fff; }}
        .btn-info {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #fff; }}
        .btn:active {{ transform: scale(0.95); }}
        .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .btn-group {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .status-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .status-live {{ background: #38ef7d; color: #000; }}
        .status-offline {{ background: #eb3349; color: #fff; }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .info-row:last-child {{ border-bottom: none; }}
        .info-label {{ opacity: 0.7; }}
        .info-value {{ font-weight: 600; }}
        .input-group {{ margin: 15px 0; }}
        .input-group label {{ display: block; margin-bottom: 8px; opacity: 0.8; }}
        .input-group input, .input-group select {{
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1rem;
        }}
        .input-group input:focus {{ outline: none; border-color: #4fc3f7; }}
        .bottom-nav {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(26,26,46,0.95);
            backdrop-filter: blur(10px);
            display: flex;
            justify-content: space-around;
            padding: 10px 0;
            border-top: 1px solid rgba(255,255,255,0.1);
            z-index: 1000;
        }}
        .nav-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: rgba(255,255,255,0.6);
            font-size: 0.75rem;
            padding: 5px 15px;
            transition: color 0.3s;
        }}
        .nav-item.active {{ color: #4fc3f7; }}
        .nav-item .icon {{ font-size: 1.5rem; margin-bottom: 3px; }}
        .log-output {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            max-height: 300px;
            overflow-y: auto;
        }}
        .log-line {{ margin: 5px 0; }}
        .progress-bar {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.3s;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.8rem; font-weight: 700; color: #4fc3f7; }}
        .stat-label {{ font-size: 0.8rem; opacity: 0.7; margin-top: 5px; }}
        .toast {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: #fff;
            padding: 12px 24px;
            border-radius: 10px;
            z-index: 2000;
            display: none;
        }}
        @media (max-width: 480px) {{
            .header h1 {{ font-size: 1.1rem; }}
            .btn {{ padding: 10px 16px; font-size: 0.9rem; }}
            .container {{ padding: 15px; }}
        }}
    </style>
    {extra_css}
</head>
<body>
    <div class="toast" id="toast"></div>
    {content}
    
    <nav class="bottom-nav">
        <a href="/" class="nav-item {'active' if page == 'home' else ''}">
            <span class="icon">🏠</span>
            <span>Home</span>
        </a>
        <a href="/streams" class="nav-item {'active' if page == 'streams' else ''}">
            <span class="icon">📡</span>
            <span>Streams</span>
        </a>
        <a href="/videos" class="nav-item {'active' if page == 'videos' else ''}">
            <span class="icon">🎬</span>
            <span>Videos</span>
        </a>
        <a href="/settings" class="nav-item {'active' if page == 'settings' else ''}">
            <span class="icon">⚙️</span>
            <span>Settings</span>
        </a>
        <a href="/monitor" class="nav-item {'active' if page == 'monitor' else ''}">
            <span class="icon">📊</span>
            <span>Monitor</span>
        </a>
    </nav>
    
    <script>
        function showToast(message, duration = 3000) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', duration);
        }}
        
        async function apiCall(endpoint, method = 'GET', data = null) {{
            const options = {{ method }};
            if (data) {{
                options.headers = {{ 'Content-Type': 'application/json' }};
                options.body = JSON.stringify(data);
            }}
            const response = await fetch(endpoint, options);
            return response.json();
        }}
        
        function formatBytes(bytes) {{
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }}
        
        function formatDuration(seconds) {{
            if (!seconds) return 'N/A';
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${{h}}:${{m.toString().padStart(2,'0')}}:${{s.toString().padStart(2,'0')}}`;
        }}
    </script>
    {extra_js}
</body>
</html>'''

# ==================== Page Content Templates ====================

HOME_CONTENT = '''
<div class="header">
    <h1>🎥 YouTube Live Manager</h1>
    <div class="status" id="headerStatus">Loading...</div>
</div>

<div class="container">
    <div class="card">
        <h2>📊 Quick Status</h2>
        <div class="grid">
            <div class="stat-card">
                <div class="stat-value" id="activeStreams">-</div>
                <div class="stat-label">Active Streams</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="ffmpegCount">-</div>
                <div class="stat-label">FFmpeg Processes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="cpuUsage">-</div>
                <div class="stat-label">CPU Usage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="memUsage">-</div>
                <div class="stat-label">Memory</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>🔴 Main Stream</h2>
        <div class="info-row">
            <span class="info-label">Session</span>
            <span class="info-value" id="mainSession">-</span>
        </div>
        <div class="info-row">
            <span class="info-label">Status</span>
            <span class="info-value" id="mainStatus">-</span>
        </div>
        <div class="info-row">
            <span class="info-label">Video</span>
            <span class="info-value" id="mainVideo">-</span>
        </div>
        <div class="btn-group" style="margin-top: 15px;">
            <button class="btn btn-success" onclick="startStream()">▶ Start</button>
            <button class="btn btn-danger" onclick="stopStream()">⏹ Stop</button>
            <button class="btn btn-warning" onclick="restartStream()">🔄 Restart</button>
        </div>
    </div>
    
    <div class="card">
        <h2>⏰ Auto-Restart</h2>
        <div class="info-row">
            <span class="info-label">Status</span>
            <span class="info-value" id="autoRestartStatus">-</span>
        </div>
        <div class="info-row">
            <span class="info-label">Interval</span>
            <span class="info-value" id="autoRestartInterval">-</span>
        </div>
        <div class="btn-group" style="margin-top: 15px;">
            <a href="/settings" class="btn btn-info">Configure</a>
            <button class="btn btn-warning" onclick="triggerRestart()">Restart Now</button>
        </div>
    </div>
    
    <div class="card">
        <h2>📋 Recent Activity</h2>
        <div class="log-output" id="recentLogs">
            <div class="log-line">Loading logs...</div>
        </div>
    </div>
</div>

<script>
async function loadStatus() {
    try {
        const status = await apiCall('/api/status');
        document.getElementById('headerStatus').textContent = status.main_stream_active ? '🟢 LIVE' : '⚫ OFFLINE';
        document.getElementById('activeStreams').textContent = status.active_streams;
        document.getElementById('ffmpegCount').textContent = status.ffmpeg_count;
        document.getElementById('cpuUsage').textContent = status.system.cpu + '%';
        document.getElementById('memUsage').textContent = status.system.memory;
        document.getElementById('mainSession').textContent = status.config.session_name;
        document.getElementById('mainStatus').innerHTML = status.main_stream_active 
            ? '<span class="status-badge status-live">LIVE</span>' 
            : '<span class="status-badge status-offline">OFFLINE</span>';
        document.getElementById('mainVideo').textContent = status.config.video_path;
        document.getElementById('autoRestartStatus').textContent = status.auto_restart.enabled ? '✓ Enabled' : '✗ Disabled';
        document.getElementById('autoRestartInterval').textContent = status.auto_restart.interval_hours + ' hours';
        if (status.logs && status.logs.length > 0) {
            document.getElementById('recentLogs').innerHTML = status.logs.map(log => `<div class="log-line">${log}</div>`).join('');
        }
    } catch (e) { console.error('Error:', e); }
}
async function startStream() { const r = await apiCall('/api/stream/start', 'POST'); showToast(r.message); setTimeout(loadStatus, 2000); }
async function stopStream() { if (!confirm('Stop stream?')) return; const r = await apiCall('/api/stream/stop', 'POST'); showToast(r.message); setTimeout(loadStatus, 2000); }
async function restartStream() { if (!confirm('Restart stream?')) return; const r = await apiCall('/api/stream/restart', 'POST'); showToast(r.message); setTimeout(loadStatus, 3000); }
async function triggerRestart() { if (!confirm('Restart all?')) return; const r = await apiCall('/api/restart', 'POST'); showToast(r.message); }
loadStatus();
setInterval(loadStatus, 10000);
</script>
'''

STREAMS_CONTENT = '''
<div class="header">
    <h1>📡 Multi-Stream Manager</h1>
    <div class="status">Manage multiple streams</div>
</div>
<div class="container">
    <div class="card">
        <h2>Add New Stream</h2>
        <div class="input-group">
            <label>Platform</label>
            <select id="platform" onchange="document.getElementById('rtmpGroup').style.display=this.value==='custom'?'block':'none'">
                <option value="youtube">YouTube</option>
                <option value="youtube_secondary">YouTube (Secondary)</option>
                <option value="facebook">Facebook</option>
                <option value="twitch">Twitch</option>
                <option value="tiktok">TikTok</option>
                <option value="custom">Custom RTMP</option>
            </select>
        </div>
        <div class="input-group"><label>Session Name</label><input type="text" id="sessionName" placeholder="my_stream"></div>
        <div class="input-group"><label>Stream Key</label><input type="password" id="streamKey" placeholder="xxxx-xxxx-xxxx"></div>
        <div class="input-group" id="rtmpGroup" style="display:none;"><label>RTMP URL</label><input type="text" id="rtmpUrl" placeholder="rtmp://..."></div>
        <div class="btn-group"><button class="btn btn-primary" onclick="addStream()">+ Add Stream</button></div>
    </div>
    <div class="card"><h2>Configured Streams</h2><div id="streamsList">Loading...</div></div>
    <div class="card"><h2>Actions</h2><div class="btn-group"><button class="btn btn-success" onclick="startAllStreams()">▶ Start All</button><button class="btn btn-danger" onclick="stopAllStreams()">⏹ Stop All</button></div></div>
</div>
<script>
async function loadStreams() {
    const config = await apiCall('/api/config/multi');
    const c = document.getElementById('streamsList');
    if (!config.streams || config.streams.length === 0) { c.innerHTML = '<p style="opacity:0.7;text-align:center;padding:20px;">No streams configured</p>'; return; }
    c.innerHTML = config.streams.map((s, i) => `<div class="card" style="margin:10px 0;padding:15px;"><div class="info-row"><span class="info-label">Platform</span><span class="info-value">${s.platform}</span></div><div class="info-row"><span class="info-label">Session</span><span class="info-value">${s.session_name}</span></div><div class="info-row"><span class="info-label">Key</span><span class="info-value">****${s.stream_key.slice(-4)}</span></div><div class="btn-group" style="margin-top:10px;"><button class="btn btn-success" onclick="startStream('${s.session_name}')">▶</button><button class="btn btn-danger" onclick="stopStream('${s.session_name}')">⏹</button><button class="btn btn-warning" onclick="removeStream(${i})">🗑</button></div></div>`).join('');
}
async function addStream() {
    const platform = document.getElementById('platform').value, session_name = document.getElementById('sessionName').value, stream_key = document.getElementById('streamKey').value, rtmp_url = document.getElementById('rtmpUrl').value;
    if (!session_name || !stream_key) { showToast('Fill required fields'); return; }
    const r = await apiCall('/api/config/multi', 'POST', { action: 'add', stream: { platform, session_name, stream_key, rtmp_url } });
    showToast(r.message); loadStreams();
}
async function removeStream(i) { if (!confirm('Remove?')) return; await apiCall('/api/config/multi', 'POST', { action: 'remove', index: i }); loadStreams(); }
async function startStream(s) { const r = await apiCall('/api/stream/start_multi', 'POST', { session: s }); showToast(r.message); }
async function stopStream(s) { const r = await apiCall('/api/stream/stop_multi', 'POST', { session: s }); showToast(r.message); }
async function startAllStreams() { const r = await apiCall('/api/stream/multi_start', 'POST'); showToast(r.message); setTimeout(loadStreams, 2000); }
async function stopAllStreams() { if (!confirm('Stop all?')) return; const r = await apiCall('/api/stream/multi_stop', 'POST'); showToast(r.message); setTimeout(loadStreams, 2000); }
loadStreams();
</script>
'''

VIDEOS_CONTENT = '''
<div class="header"><h1>🎬 Video Manager</h1><div class="status">Manage your video library</div></div>
<div class="container">
    <div class="card"><h2>Current Video</h2><div class="info-row"><span class="info-label">Path</span><span class="info-value" id="currentVideo">-</span></div><div class="input-group" style="margin-top:15px;"><label>Change Video</label><input type="text" id="videoPath" placeholder="/path/to/video.mp4"></div><div class="btn-group"><button class="btn btn-primary" onclick="setVideo()">Set Video</button><button class="btn btn-info" onclick="scanVideos()">🔍 Scan</button></div></div>
    <div class="card"><h2>Available Videos</h2><div id="videosList">Loading...</div></div>
    <div class="card"><h2>Download from Google Drive</h2><div class="input-group"><label>URL</label><input type="text" id="gdriveUrl" placeholder="https://drive.google.com/uc?id=..."></div><div class="input-group"><label>Save As</label><input type="text" id="outputPath" placeholder="/root/video.mp4"></div><div class="btn-group"><button class="btn btn-success" onclick="downloadVideo()">📥 Download</button></div></div>
</div>
<script>
async function loadVideos() {
    const config = await apiCall('/api/config'); document.getElementById('currentVideo').textContent = config.video_path;
    const videos = await apiCall('/api/videos'); const c = document.getElementById('videosList');
    if (!videos || videos.length === 0) { c.innerHTML = '<p style="opacity:0.7;text-align:center;padding:20px;">No videos found</p>'; return; }
    c.innerHTML = videos.map(v => `<div class="card" style="margin:10px 0;padding:15px;"><div class="info-row"><span class="info-label">Name</span><span class="info-value">${v.name}</span></div><div class="info-row"><span class="info-label">Path</span><span class="info-value" style="font-size:0.85rem;">${v.path}</span></div><div class="info-row"><span class="info-label">Duration</span><span class="info-value">${formatDuration(v.duration)}</span></div><div class="info-row"><span class="info-label">Size</span><span class="info-value">${formatBytes(v.size)}</span></div><div class="btn-group" style="margin-top:10px;"><button class="btn btn-primary" onclick="selectVideo('${v.path}')">Use This</button></div></div>`).join('');
}
async function setVideo() { const p = document.getElementById('videoPath').value; if (!p) { showToast('Enter path'); return; } await apiCall('/api/config', 'POST', { video_path: p }); showToast('Saved'); loadVideos(); }
async function selectVideo(p) { document.getElementById('videoPath').value = p; await setVideo(); }
async function scanVideos() { const d = prompt('Directory:', '/root'); if (!d) return; await apiCall('/api/videos/scan', 'POST', { directory: d }); loadVideos(); }
async function downloadVideo() { const u = document.getElementById('gdriveUrl').value; if (!u) { showToast('Enter URL'); return; } showToast('Downloading...'); await apiCall('/api/download', 'POST', { url: u, output: document.getElementById('outputPath').value }); showToast('Done'); }
loadVideos();
</script>
'''

SETTINGS_CONTENT = '''
<div class="header"><h1>⚙️ Settings</h1><div class="status">Configure your streams</div></div>
<div class="container">
    <div class="card"><h2>Main Config</h2><div class="input-group"><label>Stream Key</label><input type="password" id="streamKey"></div><div class="input-group"><label>Session Name</label><input type="text" id="sessionName" value="youtube_live"></div><div class="btn-group"><button class="btn btn-primary" onclick="saveConfig()">💾 Save</button></div></div>
    <div class="card"><h2>⏰ Auto-Restart</h2><div class="info-row"><span class="info-label">Status</span><span class="info-value" id="arStatus">-</span></div><div class="input-group"><label>Interval (hours)</label><input type="number" id="arInterval" min="1" max="24" value="6"></div><div class="btn-group"><button class="btn btn-success" onclick="enableAR()">Enable</button><button class="btn btn-danger" onclick="disableAR()">Disable</button><button class="btn btn-warning" onclick="setAR()">Set</button></div></div>
    <div class="card"><h2>Daemon</h2><div class="info-row"><span class="info-label">Status</span><span class="info-value" id="daemonStatus">-</span></div><div class="btn-group"><button class="btn btn-success" onclick="daemonStart()">Start</button><button class="btn btn-danger" onclick="daemonStop()">Stop</button><button class="btn btn-info" onclick="daemonCheck()">Status</button></div></div>
    <div class="card"><h2>System</h2><div class="btn-group"><button class="btn btn-info" onclick="checkDeps()">Check</button><a href="/logs" class="btn btn-warning">Logs</a></div></div>
</div>
<script>
async function loadSettings() {
    const c = await apiCall('/api/config'); document.getElementById('streamKey').value = c.stream_key || ''; document.getElementById('sessionName').value = c.session_name || 'youtube_live';
    const ar = await apiCall('/api/auto_restart/status'); document.getElementById('arStatus').textContent = ar.enabled ? '✓ Enabled' : '✗ Disabled'; document.getElementById('arInterval').value = ar.interval_hours || 6;
    const d = await apiCall('/api/daemon/status'); document.getElementById('daemonStatus').textContent = d.running ? '🟢 Running' : '⚫ Stopped';
}
async function saveConfig() { await apiCall('/api/config', 'POST', { stream_key: document.getElementById('streamKey').value, session_name: document.getElementById('sessionName').value }); showToast('Saved'); }
async function enableAR() { await apiCall('/api/auto_restart/enable', 'POST', { interval_hours: parseInt(document.getElementById('arInterval').value) }); showToast('Enabled'); loadSettings(); }
async function disableAR() { await apiCall('/api/auto_restart/disable', 'POST'); showToast('Disabled'); loadSettings(); }
async function setAR() { await apiCall('/api/auto_restart/interval', 'POST', { interval_hours: parseInt(document.getElementById('arInterval').value) }); showToast('Set'); }
async function daemonStart() { await apiCall('/api/daemon/start', 'POST'); showToast('Started'); setTimeout(loadSettings, 2000); }
async function daemonStop() { await apiCall('/api/daemon/stop', 'POST'); showToast('Stopped'); setTimeout(loadSettings, 2000); }
async function daemonCheck() { const r = await apiCall('/api/daemon/status'); showToast(r.running ? 'Running' : 'Stopped'); }
async function checkDeps() { const r = await apiCall('/api/system/check'); showToast(r.all_installed ? 'All OK' : 'Missing: ' + r.missing.join(', ')); }
loadSettings();
</script>
'''

MONITOR_CONTENT = '''
<div class="header"><h1>📊 Real-Time Monitor</h1><div class="status" id="headerStatus">Connecting...</div></div>
<div class="container">
    <div class="card"><h2>System Resources</h2><div class="info-row"><span class="info-label">CPU</span><span class="info-value" id="cpuValue">-</span></div><div class="progress-bar"><div class="progress-fill" id="cpuBar" style="width:0%"></div></div><div class="info-row"><span class="info-label">Memory</span><span class="info-value" id="memValue">-</span></div><div class="progress-bar"><div class="progress-fill" id="memBar" style="width:0%"></div></div><div class="info-row"><span class="info-label">Disk</span><span class="info-value" id="diskValue">-</span></div></div>
    <div class="card"><h2>Active Streams</h2><div id="streamsMonitor">Loading...</div></div>
    <div class="card"><h2>FFmpeg</h2><div class="info-row"><span class="info-label">Count</span><span class="info-value" id="ffmpegCount">-</span></div></div>
    <div class="card"><h2>Live Logs</h2><div class="log-output" id="liveLogs">Connecting...</div><div class="btn-group" style="margin-top:10px;"><button class="btn btn-info" onclick="toggleLogs()" id="logsBtn">Pause</button><button class="btn btn-warning" onclick="clearLogs()">Clear</button></div></div>
</div>
<script>
let logsRunning = true;
async function loadMonitor() {
    const s = await apiCall('/api/system/stats');
    document.getElementById('cpuValue').textContent = s.cpu + '%'; document.getElementById('cpuBar').style.width = s.cpu + '%';
    document.getElementById('memValue').textContent = s.memory;
    const mp = parseFloat(s.memory.match(/\\(([^)]+)\\)/)?.[1]) || 0; document.getElementById('memBar').style.width = mp + '%';
    document.getElementById('diskValue').textContent = s.disk; document.getElementById('ffmpegCount').textContent = s.ffmpeg_count;
    const sess = await apiCall('/api/sessions'); const c = document.getElementById('streamsMonitor');
    if (sess.length === 0) { c.innerHTML = '<p style="opacity:0.7;text-align:center;">No active streams</p>'; }
    else { c.innerHTML = sess.map(s => `<div class="info-row"><span class="info-label">📡 ${s}</span><span class="status-badge status-live">LIVE</span></div>`).join(''); }
    document.getElementById('headerStatus').textContent = '🟢 ' + sess.length + ' streams';
}
async function loadLogs() { if (!logsRunning) return; const logs = await apiCall('/api/logs/recent'); const c = document.getElementById('liveLogs'); if (logs && logs.length > 0) { c.innerHTML = logs.map(l => `<div class="log-line">${l}</div>`).join(''); c.scrollTop = c.scrollHeight; } }
function toggleLogs() { logsRunning = !logsRunning; document.getElementById('logsBtn').textContent = logsRunning ? 'Pause' : 'Resume'; }
function clearLogs() { document.getElementById('liveLogs').innerHTML = '<div class="log-line">Cleared</div>'; }
loadMonitor(); loadLogs(); setInterval(loadMonitor, 5000); setInterval(loadLogs, 3000);
</script>
'''

LOGS_CONTENT = '''
<div class="header"><h1>📋 System Logs</h1><div class="status">View and manage logs</div></div>
<div class="container">
    <div class="card"><h2>Logs</h2><div class="input-group"><label>Filter</label><input type="text" id="sessionFilter" placeholder="Session" onkeyup="loadLogs()"></div><div class="log-output" id="logsContainer" style="max-height:500px;">Loading...</div></div>
    <div class="card"><h2>Actions</h2><div class="btn-group"><button class="btn btn-info" onclick="loadLogs()">🔄 Refresh</button><button class="btn btn-warning" onclick="clearLogs()">🗑 Clear</button></div></div>
</div>
<script>
async function loadLogs() { const f = document.getElementById('sessionFilter').value; const logs = await apiCall('/api/logs', 'POST', { filter: f }); const c = document.getElementById('logsContainer'); c.innerHTML = logs.length === 0 ? '<p style="opacity:0.7;text-align:center;padding:20px;">No logs</p>' : logs.map(l => `<div class="log-line">${l}</div>`).join(''); }
async function clearLogs() { if (!confirm('Clear all?')) return; await apiCall('/api/logs/clear', 'POST'); showToast('Cleared'); loadLogs(); }
loadLogs();
</script>
'''

# ==================== Routes ====================

@app.route('/')
def home():
    return get_base_html(title="Home - YouTube Live", content=HOME_CONTENT, page='home')

@app.route('/streams')
def streams():
    return get_base_html(title="Streams - YouTube Live", content=STREAMS_CONTENT, page='streams')

@app.route('/videos')
def videos():
    return get_base_html(title="Videos - YouTube Live", content=VIDEOS_CONTENT, page='videos')

@app.route('/settings')
def settings():
    return get_base_html(title="Settings - YouTube Live", content=SETTINGS_CONTENT, page='settings')

@app.route('/monitor')
def monitor():
    return get_base_html(title="Monitor - YouTube Live", content=MONITOR_CONTENT, page='monitor')

@app.route('/logs')
def logs_page():
    return get_base_html(title="Logs - YouTube Live", content=LOGS_CONTENT, page='logs')

# ==================== API Endpoints ====================

@app.route('/api/status')
def api_status():
    config = load_config()
    auto_restart = load_auto_restart_config()
    main_active = get_session_status(config.get('session_name', 'youtube_live'))
    active_sessions = get_all_sessions()
    system = get_system_stats()
    logs = get_recent_logs(limit=5)
    log_lines = []
    for log in logs:
        log_lines.extend(read_log_tail(log, 2))
    return jsonify({
        'main_stream_active': main_active,
        'active_streams': len([s for s in active_sessions if 'live' in s.lower() or 'stream' in s.lower()]),
        'ffmpeg_count': get_ffmpeg_process_count(),
        'config': {'session_name': config.get('session_name', 'youtube_live'), 'video_path': config.get('video_path', DEFAULT_VIDEO_PATH), 'stream_key_set': bool(config.get('stream_key'))},
        'auto_restart': {'enabled': auto_restart.get('enabled', False), 'interval_hours': auto_restart.get('interval_hours', 6)},
        'system': system,
        'logs': log_lines[-5:]
    })

@app.route('/api/config')
def api_get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def api_set_config():
    data = request.json or {}
    config = load_config()
    if 'stream_key' in data: config['stream_key'] = data['stream_key']
    if 'video_path' in data: config['video_path'] = data['video_path']
    if 'session_name' in data: config['session_name'] = data['session_name']
    save_config(config)
    return jsonify({'message': 'Configuration saved', 'success': True})

@app.route('/api/config/multi')
def api_get_multi():
    return jsonify(load_multi_config())

@app.route('/api/config/multi', methods=['POST'])
def api_set_multi():
    data = request.json or {}
    config = load_multi_config()
    if data.get('action') == 'add': config['streams'].append(data['stream'])
    elif data.get('action') == 'remove':
        idx = data.get('index', -1)
        if 0 <= idx < len(config['streams']): config['streams'].pop(idx)
    save_multi_config(config)
    return jsonify({'message': 'Updated', 'success': True})

@app.route('/api/videos')
def api_videos():
    return jsonify(get_video_list(load_config()))

@app.route('/api/videos/scan', methods=['POST'])
def api_scan():
    data = request.json or {}
    videos = scan_video_directory(data.get('directory', '/root'))
    return jsonify({'message': f'Found {len(videos)} videos', 'videos': videos, 'success': True})

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.json or {}
    url = data.get('url', '')
    if not url: return jsonify({'message': 'URL required', 'success': False})
    try:
        cmd = ['gdown', url]
        if data.get('output'): cmd.extend(['-O', data['output']])
        subprocess.run(cmd, check=True, timeout=3600)
        return jsonify({'message': 'Download complete', 'success': True})
    except Exception as e:
        return jsonify({'message': f'Failed: {e}', 'success': False})

@app.route('/api/stream/start', methods=['POST'])
def api_start():
    config = load_config()
    session = config.get('session_name', 'youtube_live')
    if get_session_status(session): return jsonify({'message': 'Already running', 'success': False})
    from youtube_live import start_stream
    return jsonify({'message': 'Started' if start_stream() else 'Failed', 'success': True})

@app.route('/api/stream/stop', methods=['POST'])
def api_stop():
    session = load_config().get('session_name', 'youtube_live')
    if not get_session_status(session): return jsonify({'message': 'Not running', 'success': False})
    stop_session(session)
    return jsonify({'message': 'Stopped', 'success': True})

@app.route('/api/stream/restart', methods=['POST'])
def api_restart():
    config = load_config()
    session = config.get('session_name', 'youtube_live')
    if get_session_status(session): stop_session(session); time.sleep(2)
    from youtube_live import start_stream
    return jsonify({'message': 'Restarted' if start_stream() else 'Failed', 'success': True})

@app.route('/api/stream/multi_start', methods=['POST'])
def api_multi_start():
    from youtube_live import start_multi_stream
    return jsonify({'message': 'Started' if start_multi_stream() else 'Failed', 'success': True})

@app.route('/api/stream/multi_stop', methods=['POST'])
def api_multi_stop():
    from youtube_live import stop_multi_stream
    return jsonify({'message': 'Stopped' if stop_multi_stream() else 'Failed', 'success': True})

@app.route('/api/stream/start_multi', methods=['POST'])
def api_start_multi():
    data = request.json or {}
    session = data.get('session', '')
    if not session: return jsonify({'message': 'Session required', 'success': False})
    from youtube_live import start_multi_stream
    return jsonify({'message': 'Started' if start_multi_stream() else 'Failed', 'success': True})

@app.route('/api/stream/stop_multi', methods=['POST'])
def api_stop_multi():
    data = request.json or {}
    session = data.get('session', '')
    if session: stop_session(session)
    return jsonify({'message': 'Stopped', 'success': True})

@app.route('/api/sessions')
def api_sessions():
    return jsonify(get_all_sessions())

@app.route('/api/logs')
def api_logs():
    data = request.json or {}
    logs = get_recent_logs(session_name=data.get('filter'), limit=20) if data.get('filter') else get_recent_logs(limit=20)
    result = []
    for log in logs: result.extend(read_log_tail(log, 10))
    return jsonify(result[-50:])

@app.route('/api/logs/recent')
def api_recent():
    logs = get_recent_logs(limit=3)
    result = []
    for log in logs: result.extend(read_log_tail(log, 5))
    return jsonify(result[-15:])

@app.route('/api/logs/clear', methods=['POST'])
def api_clear():
    if DEFAULT_LOG_DIR.exists():
        for log in DEFAULT_LOG_DIR.glob('*.log'): log.unlink()
    return jsonify({'message': 'Cleared', 'success': True})

@app.route('/api/auto_restart/status')
def api_ar_status():
    return jsonify(load_auto_restart_config())

@app.route('/api/auto_restart/enable', methods=['POST'])
def api_ar_enable():
    data = request.json or {}
    config = load_auto_restart_config()
    config['enabled'] = True
    config['interval_hours'] = data.get('interval_hours', 6)
    save_auto_restart_config(config)
    return jsonify({'message': 'Enabled', 'success': True})

@app.route('/api/auto_restart/disable', methods=['POST'])
def api_ar_disable():
    config = load_auto_restart_config()
    config['enabled'] = False
    save_auto_restart_config(config)
    return jsonify({'message': 'Disabled', 'success': True})

@app.route('/api/auto_restart/interval', methods=['POST'])
def api_ar_interval():
    data = request.json or {}
    config = load_auto_restart_config()
    config['interval_hours'] = data.get('interval_hours', 6)
    save_auto_restart_config(config)
    return jsonify({'message': 'Updated', 'success': True})

@app.route('/api/restart', methods=['POST'])
def api_restart_all():
    from youtube_live import auto_restart_all_streams
    auto_restart_all_streams()
    return jsonify({'message': 'Restarting', 'success': True})

@app.route('/api/daemon/start', methods=['POST'])
def api_daemon_start():
    subprocess.run(['python3', str(Path(__file__).parent / 'auto_restart_daemon.py'), 'start'], capture_output=True)
    return jsonify({'message': 'Daemon started', 'success': True})

@app.route('/api/daemon/stop', methods=['POST'])
def api_daemon_stop():
    subprocess.run(['python3', str(Path(__file__).parent / 'auto_restart_daemon.py'), 'stop'], capture_output=True)
    return jsonify({'message': 'Daemon stopped', 'success': True})

@app.route('/api/daemon/status')
def api_daemon_status():
    result = subprocess.run(['python3', str(Path(__file__).parent / 'auto_restart_daemon.py'), 'status'], capture_output=True, text=True)
    return jsonify({'running': 'running' in result.stdout.lower() or 'running' in result.stderr.lower(), 'output': result.stdout})

@app.route('/api/system/stats')
def api_sys_stats():
    s = get_system_stats()
    s['ffmpeg_count'] = get_ffmpeg_process_count()
    return jsonify(s)

@app.route('/api/system/check')
def api_sys_check():
    ok, missing = check_dependencies()
    return jsonify({'all_installed': ok, 'missing': missing})

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--port', type=int, default=5000)
    p.add_argument('--debug', action='store_true')
    args = p.parse_args()
    print(f"Starting dashboard on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
