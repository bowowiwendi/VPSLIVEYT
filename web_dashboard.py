#!/usr/bin/env python3
"""
YouTube Live Streaming - Web Dashboard
Mobile-friendly web interface for managing live streams.
"""

from flask import Flask, render_template_string, jsonify, request, redirect, url_for
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
import sys

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import *

app = Flask(__name__)

# ==================== HTML Templates ====================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}YouTube Live Manager{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding-bottom: 80px;
        }
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { font-size: 1.3rem; color: #fff; }
        .header .status { font-size: 0.85rem; opacity: 0.8; margin-top: 5px; }
        .container { padding: 20px; max-width: 800px; margin: 0 auto; }
        .card {
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 { font-size: 1.1rem; margin-bottom: 15px; color: #4fc3f7; }
        .card h3 { font-size: 1rem; margin: 15px 0 10px; color: #81d4fa; }
        .btn {
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
        }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }
        .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: #fff; }
        .btn-danger { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: #fff; }
        .btn-warning { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #fff; }
        .btn-info { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #fff; }
        .btn:active { transform: scale(0.95); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-group { display: flex; flex-wrap: wrap; gap: 10px; }
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-live { background: #38ef7d; color: #000; }
        .status-offline { background: #eb3349; color: #fff; }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .info-row:last-child { border-bottom: none; }
        .info-label { opacity: 0.7; }
        .info-value { font-weight: 600; }
        .input-group { margin: 15px 0; }
        .input-group label { display: block; margin-bottom: 8px; opacity: 0.8; }
        .input-group input, .input-group select {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1rem;
        }
        .input-group input:focus { outline: none; border-color: #4fc3f7; }
        .bottom-nav {
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
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: rgba(255,255,255,0.6);
            font-size: 0.75rem;
            padding: 5px 15px;
            transition: color 0.3s;
        }
        .nav-item.active { color: #4fc3f7; }
        .nav-item .icon { font-size: 1.5rem; margin-bottom: 3px; }
        .log-output {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-line { margin: 5px 0; }
        .progress-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.3s;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }
        .stat-value { font-size: 1.8rem; font-weight: 700; color: #4fc3f7; }
        .stat-label { font-size: 0.8rem; opacity: 0.7; margin-top: 5px; }
        .toast {
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
        }
        @media (max-width: 480px) {
            .header h1 { font-size: 1.1rem; }
            .btn { padding: 10px 16px; font-size: 0.9rem; }
            .container { padding: 15px; }
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="toast" id="toast"></div>
    {% block content %}{% endblock %}
    
    <nav class="bottom-nav">
        <a href="/" class="nav-item {% if page == 'home' %}active{% endif %}">
            <span class="icon">🏠</span>
            <span>Home</span>
        </a>
        <a href="/streams" class="nav-item {% if page == 'streams' %}active{% endif %}">
            <span class="icon">📡</span>
            <span>Streams</span>
        </a>
        <a href="/videos" class="nav-item {% if page == 'videos' %}active{% endif %}">
            <span class="icon">🎬</span>
            <span>Videos</span>
        </a>
        <a href="/settings" class="nav-item {% if page == 'settings' %}active{% endif %}">
            <span class="icon">⚙️</span>
            <span>Settings</span>
        </a>
        <a href="/monitor" class="nav-item {% if page == 'monitor' %}active{% endif %}">
            <span class="icon">📊</span>
            <span>Monitor</span>
        </a>
    </nav>
    
    <script>
        function showToast(message, duration = 3000) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', duration);
        }
        
        async function apiCall(endpoint, method = 'GET', data = null) {
            const options = { method };
            if (data) {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = JSON.stringify(data);
            }
            const response = await fetch(endpoint, options);
            return response.json();
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function formatDuration(seconds) {
            if (!seconds) return 'N/A';
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }
    </script>
    {% block extra_js %}{% endblock %}
</body>
</html>
'''

HOME_TEMPLATE = '''
{% extends "base" %}
{% block title %}Home - YouTube Live Manager{% endblock %}
{% block content %}
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
{% endblock %}

{% block extra_js %}
<script>
async function loadStatus() {
    try {
        const status = await apiCall('/api/status');
        
        document.getElementById('headerStatus').textContent = 
            status.main_stream_active ? '🟢 LIVE' : '⚫ OFFLINE';
        
        document.getElementById('activeStreams').textContent = status.active_streams;
        document.getElementById('ffmpegCount').textContent = status.ffmpeg_count;
        document.getElementById('cpuUsage').textContent = status.system.cpu + '%';
        document.getElementById('memUsage').textContent = status.system.memory;
        
        document.getElementById('mainSession').textContent = status.config.session_name;
        document.getElementById('mainStatus').innerHTML = status.main_stream_active 
            ? '<span class="status-badge status-live">LIVE</span>' 
            : '<span class="status-badge status-offline">OFFLINE</span>';
        document.getElementById('mainVideo').textContent = status.config.video_path;
        
        document.getElementById('autoRestartStatus').textContent = 
            status.auto_restart.enabled ? '✓ Enabled' : '✗ Disabled';
        document.getElementById('autoRestartInterval').textContent = 
            status.auto_restart.interval_hours + ' hours';
        
        if (status.logs && status.logs.length > 0) {
            document.getElementById('recentLogs').innerHTML = 
                status.logs.map(log => `<div class="log-line">${log}</div>`).join('');
        }
    } catch (e) {
        console.error('Error loading status:', e);
    }
}

async function startStream() {
    const result = await apiCall('/api/stream/start', 'POST');
    showToast(result.message);
    setTimeout(loadStatus, 2000);
}

async function stopStream() {
    if (!confirm('Stop current stream?')) return;
    const result = await apiCall('/api/stream/stop', 'POST');
    showToast(result.message);
    setTimeout(loadStatus, 2000);
}

async function restartStream() {
    if (!confirm('Restart current stream?')) return;
    const result = await apiCall('/api/stream/restart', 'POST');
    showToast(result.message);
    setTimeout(loadStatus, 3000);
}

async function triggerRestart() {
    if (!confirm('Restart all streams now?')) return;
    const result = await apiCall('/api/restart', 'POST');
    showToast(result.message);
}

loadStatus();
setInterval(loadStatus, 10000);
</script>
{% endblock %}
'''

STREAMS_TEMPLATE = '''
{% extends "base" %}
{% block title %}Streams - YouTube Live Manager{% endblock %}
{% block content %}
<div class="header">
    <h1>📡 Multi-Stream Manager</h1>
    <div class="status">Manage multiple streams</div>
</div>

<div class="container">
    <div class="card">
        <h2>Add New Stream</h2>
        <div class="input-group">
            <label>Platform</label>
            <select id="platform">
                <option value="youtube">YouTube</option>
                <option value="youtube_secondary">YouTube (Secondary)</option>
                <option value="facebook">Facebook</option>
                <option value="twitch">Twitch</option>
                <option value="tiktok">TikTok</option>
                <option value="custom">Custom RTMP</option>
            </select>
        </div>
        <div class="input-group">
            <label>Session Name</label>
            <input type="text" id="sessionName" placeholder="my_stream">
        </div>
        <div class="input-group">
            <label>Stream Key</label>
            <input type="password" id="streamKey" placeholder="xxxx-xxxx-xxxx">
        </div>
        <div class="input-group" id="rtmpGroup" style="display:none;">
            <label>RTMP URL</label>
            <input type="text" id="rtmpUrl" placeholder="rtmp://...">
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="addStream()">+ Add Stream</button>
        </div>
    </div>
    
    <div class="card">
        <h2>Configured Streams</h2>
        <div id="streamsList">Loading...</div>
    </div>
    
    <div class="card">
        <h2>Actions</h2>
        <div class="btn-group">
            <button class="btn btn-success" onclick="startAllStreams()">▶ Start All</button>
            <button class="btn btn-danger" onclick="stopAllStreams()">⏹ Stop All</button>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.getElementById('platform').addEventListener('change', function() {
    document.getElementById('rtmpGroup').style.display = this.value === 'custom' ? 'block' : 'none';
});

async function loadStreams() {
    const config = await apiCall('/api/config/multi');
    const container = document.getElementById('streamsList');
    
    if (!config.streams || config.streams.length === 0) {
        container.innerHTML = '<p style="opacity:0.7;text-align:center;padding:20px;">No streams configured</p>';
        return;
    }
    
    container.innerHTML = config.streams.map((stream, i) => `
        <div class="card" style="margin:10px 0;padding:15px;">
            <div class="info-row">
                <span class="info-label">Platform</span>
                <span class="info-value">${stream.platform}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Session</span>
                <span class="info-value">${stream.session_name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Key</span>
                <span class="info-value">****${stream.stream_key.slice(-4)}</span>
            </div>
            <div class="btn-group" style="margin-top:10px;">
                <button class="btn btn-success" onclick="startStream('${stream.session_name}')">▶</button>
                <button class="btn btn-danger" onclick="stopStream('${stream.session_name}')">⏹</button>
                <button class="btn btn-warning" onclick="removeStream(${i})">🗑</button>
            </div>
        </div>
    `).join('');
}

async function addStream() {
    const platform = document.getElementById('platform').value;
    const session_name = document.getElementById('sessionName').value;
    const stream_key = document.getElementById('streamKey').value;
    const rtmp_url = document.getElementById('rtmpUrl').value;
    
    if (!session_name || !stream_key) {
        showToast('Please fill in all required fields');
        return;
    }
    
    const result = await apiCall('/api/config/multi', 'POST', {
        action: 'add',
        stream: { platform, session_name, stream_key, rtmp_url }
    });
    
    showToast(result.message);
    loadStreams();
}

async function removeStream(index) {
    if (!confirm('Remove this stream?')) return;
    const result = await apiCall('/api/config/multi', 'POST', { action: 'remove', index });
    showToast(result.message);
    loadStreams();
}

async function startStream(session) {
    const result = await apiCall('/api/stream/start_multi', 'POST', { session });
    showToast(result.message);
}

async function stopStream(session) {
    const result = await apiCall('/api/stream/stop_multi', 'POST', { session });
    showToast(result.message);
}

async function startAllStreams() {
    const result = await apiCall('/api/stream/multi_start', 'POST');
    showToast(result.message);
    setTimeout(loadStreams, 2000);
}

async function stopAllStreams() {
    if (!confirm('Stop all streams?')) return;
    const result = await apiCall('/api/stream/multi_stop', 'POST');
    showToast(result.message);
    setTimeout(loadStreams, 2000);
}

loadStreams();
</script>
{% endblock %}
'''

VIDEOS_TEMPLATE = '''
{% extends "base" %}
{% block title %}Videos - YouTube Live Manager{% endblock %}
{% block content %}
<div class="header">
    <h1>🎬 Video Manager</h1>
    <div class="status">Manage your video library</div>
</div>

<div class="container">
    <div class="card">
        <h2>Current Video</h2>
        <div class="info-row">
            <span class="info-label">Path</span>
            <span class="info-value" id="currentVideo">-</span>
        </div>
        <div class="input-group" style="margin-top:15px;">
            <label>Change Video</label>
            <input type="text" id="videoPath" placeholder="/path/to/video.mp4">
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="setVideo()">Set Video</button>
            <button class="btn btn-info" onclick="scanVideos()">🔍 Scan Directory</button>
        </div>
    </div>
    
    <div class="card">
        <h2>Available Videos</h2>
        <div id="videosList">Loading...</div>
    </div>
    
    <div class="card">
        <h2>Add Video from Google Drive</h2>
        <div class="input-group">
            <label>Google Drive URL</label>
            <input type="text" id="gdriveUrl" placeholder="https://drive.google.com/uc?id=...">
        </div>
        <div class="input-group">
            <label>Save As (optional)</label>
            <input type="text" id="outputPath" placeholder="/root/video.mp4">
        </div>
        <div class="btn-group">
            <button class="btn btn-success" onclick="downloadVideo()">📥 Download</button>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
async function loadVideos() {
    const config = await apiCall('/api/config');
    document.getElementById('currentVideo').textContent = config.video_path;
    
    const videos = await apiCall('/api/videos');
    const container = document.getElementById('videosList');
    
    if (!videos || videos.length === 0) {
        container.innerHTML = '<p style="opacity:0.7;text-align:center;padding:20px;">No videos found</p>';
        return;
    }
    
    container.innerHTML = videos.map(video => `
        <div class="card" style="margin:10px 0;padding:15px;">
            <div class="info-row">
                <span class="info-label">Name</span>
                <span class="info-value">${video.name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Path</span>
                <span class="info-value" style="font-size:0.85rem;">${video.path}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Duration</span>
                <span class="info-value">${formatDuration(video.duration)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Size</span>
                <span class="info-value">${formatBytes(video.size)}</span>
            </div>
            <div class="btn-group" style="margin-top:10px;">
                <button class="btn btn-primary" onclick="selectVideo('${video.path}')">Use This</button>
            </div>
        </div>
    `).join('');
}

async function setVideo() {
    const path = document.getElementById('videoPath').value;
    if (!path) {
        showToast('Please enter a video path');
        return;
    }
    const result = await apiCall('/api/config', 'POST', { video_path: path });
    showToast(result.message);
    loadVideos();
}

async function selectVideo(path) {
    document.getElementById('videoPath').value = path;
    await setVideo();
}

async function scanVideos() {
    const dir = prompt('Directory to scan:', '/root');
    if (!dir) return;
    const result = await apiCall('/api/videos/scan', 'POST', { directory: dir });
    showToast(result.message);
    loadVideos();
}

async function downloadVideo() {
    const url = document.getElementById('gdriveUrl').value;
    const output = document.getElementById('outputPath').value;
    
    if (!url) {
        showToast('Please enter a Google Drive URL');
        return;
    }
    
    showToast('Starting download...');
    const result = await apiCall('/api/download', 'POST', { url, output });
    showToast(result.message);
}

loadVideos();
</script>
{% endblock %}
'''

SETTINGS_TEMPLATE = '''
{% extends "base" %}
{% block title %}Settings - YouTube Live Manager{% endblock %}
{% block content %}
<div class="header">
    <h1>⚙️ Settings</h1>
    <div class="status">Configure your streams</div>
</div>

<div class="container">
    <div class="card">
        <h2>Main Configuration</h2>
        <div class="input-group">
            <label>Stream Key</label>
            <input type="password" id="streamKey" placeholder="xxxx-xxxx-xxxx">
        </div>
        <div class="input-group">
            <label>Session Name</label>
            <input type="text" id="sessionName" placeholder="youtube_live">
        </div>
        <div class="btn-group">
            <button class="btn btn-primary" onclick="saveConfig()">💾 Save</button>
        </div>
    </div>
    
    <div class="card">
        <h2>⏰ Auto-Restart Settings</h2>
        <div class="info-row">
            <span class="info-label">Status</span>
            <span class="info-value" id="arStatus">-</span>
        </div>
        <div class="input-group">
            <label>Interval (hours)</label>
            <input type="number" id="arInterval" min="1" max="24" value="6">
        </div>
        <div class="btn-group">
            <button class="btn btn-success" onclick="enableAutoRestart()">Enable</button>
            <button class="btn btn-danger" onclick="disableAutoRestart()">Disable</button>
            <button class="btn btn-warning" onclick="setInterval()">Set Interval</button>
        </div>
    </div>
    
    <div class="card">
        <h2>Daemon Control</h2>
        <div class="info-row">
            <span class="info-label">Daemon Status</span>
            <span class="info-value" id="daemonStatus">-</span>
        </div>
        <div class="btn-group">
            <button class="btn btn-success" onclick="daemonStart()">Start Daemon</button>
            <button class="btn btn-danger" onclick="daemonStop()">Stop Daemon</button>
            <button class="btn btn-info" onclick="daemonStatus()">Check Status</button>
        </div>
    </div>
    
    <div class="card">
        <h2>System</h2>
        <div class="btn-group">
            <button class="btn btn-info" onclick="checkDeps()">Check Dependencies</button>
            <a href="/logs" class="btn btn-warning">View Logs</a>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
async function loadSettings() {
    const config = await apiCall('/api/config');
    document.getElementById('streamKey').value = config.stream_key || '';
    document.getElementById('sessionName').value = config.session_name || 'youtube_live';
    
    const ar = await apiCall('/api/auto_restart/status');
    document.getElementById('arStatus').textContent = ar.enabled ? '✓ Enabled' : '✗ Disabled';
    document.getElementById('arInterval').value = ar.interval_hours || 6;
    
    const daemon = await apiCall('/api/daemon/status');
    document.getElementById('daemonStatus').textContent = daemon.running ? '🟢 Running' : '⚫ Stopped';
}

async function saveConfig() {
    const result = await apiCall('/api/config', 'POST', {
        stream_key: document.getElementById('streamKey').value,
        session_name: document.getElementById('sessionName').value
    });
    showToast(result.message);
}

async function enableAutoRestart() {
    const result = await apiCall('/api/auto_restart/enable', 'POST', {
        interval_hours: parseInt(document.getElementById('arInterval').value)
    });
    showToast(result.message);
    loadSettings();
}

async function disableAutoRestart() {
    const result = await apiCall('/api/auto_restart/disable', 'POST');
    showToast(result.message);
    loadSettings();
}

async function setInterval() {
    const result = await apiCall('/api/auto_restart/interval', 'POST', {
        interval_hours: parseInt(document.getElementById('arInterval').value)
    });
    showToast(result.message);
}

async function daemonStart() {
    const result = await apiCall('/api/daemon/start', 'POST');
    showToast(result.message);
    setTimeout(loadSettings, 2000);
}

async function daemonStop() {
    const result = await apiCall('/api/daemon/stop', 'POST');
    showToast(result.message);
    setTimeout(loadSettings, 2000);
}

async function daemonStatus() {
    const result = await apiCall('/api/daemon/status');
    showToast(result.running ? 'Daemon is running' : 'Daemon is stopped');
}

async function checkDeps() {
    const result = await apiCall('/api/system/check');
    showToast(result.all_installed ? 'All dependencies installed' : 'Missing: ' + result.missing.join(', '));
}

loadSettings();
</script>
{% endblock %}
'''

MONITOR_TEMPLATE = '''
{% extends "base" %}
{% block title %}Monitor - YouTube Live Manager{% endblock %}
{% block content %}
<div class="header">
    <h1>📊 Real-Time Monitor</h1>
    <div class="status" id="headerStatus">Connecting...</div>
</div>

<div class="container">
    <div class="card">
        <h2>System Resources</h2>
        <div class="info-row">
            <span class="info-label">CPU Usage</span>
            <span class="info-value" id="cpuValue">-</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" id="cpuBar" style="width: 0%"></div>
        </div>
        
        <div class="info-row">
            <span class="info-label">Memory</span>
            <span class="info-value" id="memValue">-</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" id="memBar" style="width: 0%"></div>
        </div>
        
        <div class="info-row">
            <span class="info-label">Disk</span>
            <span class="info-value" id="diskValue">-</span>
        </div>
    </div>
    
    <div class="card">
        <h2>Active Streams</h2>
        <div id="streamsMonitor">Loading...</div>
    </div>
    
    <div class="card">
        <h2>FFmpeg Processes</h2>
        <div class="info-row">
            <span class="info-label">Count</span>
            <span class="info-value" id="ffmpegCount">-</span>
        </div>
        <div class="log-output" id="ffmpegProcesses" style="margin-top:10px;">
            Loading...
        </div>
    </div>
    
    <div class="card">
        <h2>Live Logs</h2>
        <div class="log-output" id="liveLogs">
            Connecting...
        </div>
        <div class="btn-group" style="margin-top:10px;">
            <button class="btn btn-info" onclick="toggleLogs()" id="logsBtn">Pause</button>
            <button class="btn btn-warning" onclick="clearLogs()">Clear</button>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
let logsRunning = true;
let logsInterval;

async function loadMonitor() {
    const stats = await apiCall('/api/system/stats');
    
    document.getElementById('cpuValue').textContent = stats.cpu + '%';
    document.getElementById('cpuBar').style.width = stats.cpu + '%';
    
    document.getElementById('memValue').textContent = stats.memory;
    const memPercent = parseFloat(stats.memory.match(/\\(([^)]+)\\)/)?.[1]) || 0;
    document.getElementById('memBar').style.width = memPercent + '%';
    
    document.getElementById('diskValue').textContent = stats.disk;
    document.getElementById('ffmpegCount').textContent = stats.ffmpeg_count;
    
    const sessions = await apiCall('/api/sessions');
    const container = document.getElementById('streamsMonitor');
    
    if (sessions.length === 0) {
        container.innerHTML = '<p style="opacity:0.7;text-align:center;">No active streams</p>';
    } else {
        container.innerHTML = sessions.map(s => `
            <div class="info-row">
                <span class="info-label">📡 ${s}</span>
                <span class="status-badge status-live">LIVE</span>
            </div>
        `).join('');
    }
    
    document.getElementById('headerStatus').textContent = `🟢 ${sessions.length} streams active`;
}

async function loadLogs() {
    if (!logsRunning) return;
    const logs = await apiCall('/api/logs/recent');
    const container = document.getElementById('liveLogs');
    
    if (logs && logs.length > 0) {
        container.innerHTML = logs.map(log => `<div class="log-line">${log}</div>`).join('');
        container.scrollTop = container.scrollHeight;
    }
}

function toggleLogs() {
    logsRunning = !logsRunning;
    document.getElementById('logsBtn').textContent = logsRunning ? 'Pause' : 'Resume';
    if (logsRunning) loadLogs();
}

function clearLogs() {
    document.getElementById('liveLogs').innerHTML = '<div class="log-line">Logs cleared</div>';
}

loadMonitor();
loadLogs();
setInterval(loadMonitor, 5000);
setInterval(loadLogs, 3000);
</script>
{% endblock %}
'''

LOGS_TEMPLATE = '''
{% extends "base" %}
{% block title %}Logs - YouTube Live Manager{% endblock %}
{% block content %}
<div class="header">
    <h1>📋 System Logs</h1>
    <div class="status">View and manage logs</div>
</div>

<div class="container">
    <div class="card">
        <h2>Recent Logs</h2>
        <div class="input-group">
            <label>Filter by Session</label>
            <input type="text" id="sessionFilter" placeholder="Session name" onkeyup="loadLogs()">
        </div>
        <div class="log-output" id="logsContainer" style="max-height:500px;">
            Loading...
        </div>
    </div>
    
    <div class="card">
        <h2>Actions</h2>
        <div class="btn-group">
            <button class="btn btn-info" onclick="loadLogs()">🔄 Refresh</button>
            <button class="btn btn-warning" onclick="clearLogs()">🗑 Clear All Logs</button>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
async function loadLogs() {
    const filter = document.getElementById('sessionFilter').value;
    const logs = await apiCall('/api/logs', 'POST', { filter });
    
    const container = document.getElementById('logsContainer');
    if (logs.length === 0) {
        container.innerHTML = '<p style="opacity:0.7;text-align:center;padding:20px;">No logs found</p>';
    } else {
        container.innerHTML = logs.map(log => `<div class="log-line">${log}</div>`).join('');
    }
}

async function clearLogs() {
    if (!confirm('Clear all logs? This cannot be undone.')) return;
    await apiCall('/api/logs/clear', 'POST');
    showToast('Logs cleared');
    loadLogs();
}

loadLogs();
</script>
{% endblock %}
'''

# ==================== API Routes ====================

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE.replace('{% extends "base" %}', BASE_TEMPLATE), page='home')

@app.route('/streams')
def streams():
    return render_template_string(STREAMS_TEMPLATE.replace('{% extends "base" %}', BASE_TEMPLATE), page='streams')

@app.route('/videos')
def videos():
    return render_template_string(VIDEOS_TEMPLATE.replace('{% extends "base" %}', BASE_TEMPLATE), page='videos')

@app.route('/settings')
def settings():
    return render_template_string(SETTINGS_TEMPLATE.replace('{% extends "base" %}', BASE_TEMPLATE), page='settings')

@app.route('/monitor')
def monitor():
    return render_template_string(MONITOR_TEMPLATE.replace('{% extends "base" %}', BASE_TEMPLATE), page='monitor')

@app.route('/logs')
def logs():
    return render_template_string(LOGS_TEMPLATE.replace('{% extends "base" %}', BASE_TEMPLATE), page='logs')

# API Endpoints
@app.route('/api/status')
def api_status():
    config = load_config()
    multi_config = load_multi_config()
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
        'config': {
            'session_name': config.get('session_name', 'youtube_live'),
            'video_path': config.get('video_path', DEFAULT_VIDEO_PATH),
            'stream_key_set': bool(config.get('stream_key'))
        },
        'auto_restart': {
            'enabled': auto_restart.get('enabled', False),
            'interval_hours': auto_restart.get('interval_hours', 6)
        },
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
    
    if 'stream_key' in data:
        config['stream_key'] = data['stream_key']
    if 'video_path' in data:
        config['video_path'] = data['video_path']
    if 'session_name' in data:
        config['session_name'] = data['session_name']
    
    save_config(config)
    return jsonify({'message': 'Configuration saved', 'success': True})

@app.route('/api/config/multi')
def api_get_multi_config():
    return jsonify(load_multi_config())

@app.route('/api/config/multi', methods=['POST'])
def api_set_multi_config():
    data = request.json or {}
    config = load_multi_config()
    
    if data.get('action') == 'add':
        config['streams'].append(data['stream'])
    elif data.get('action') == 'remove':
        idx = data.get('index', -1)
        if 0 <= idx < len(config['streams']):
            config['streams'].pop(idx)
    
    save_multi_config(config)
    return jsonify({'message': 'Configuration updated', 'success': True})

@app.route('/api/videos')
def api_get_videos():
    config = load_config()
    return jsonify(get_video_list(config))

@app.route('/api/videos/scan', methods=['POST'])
def api_scan_videos():
    data = request.json or {}
    directory = data.get('directory', '/root')
    videos = scan_video_directory(directory)
    return jsonify({'message': f'Found {len(videos)} videos', 'videos': videos, 'success': True})

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.json or {}
    url = data.get('url', '')
    output = data.get('output', '')
    
    if not url:
        return jsonify({'message': 'URL required', 'success': False})
    
    try:
        cmd = ['gdown', url]
        if output:
            cmd.extend(['-O', output])
        subprocess.run(cmd, check=True, timeout=3600)
        return jsonify({'message': 'Download complete', 'success': True})
    except Exception as e:
        return jsonify({'message': f'Download failed: {e}', 'success': False})

@app.route('/api/stream/start', methods=['POST'])
def api_start_stream():
    config = load_config()
    session = config.get('session_name', 'youtube_live')
    
    if get_session_status(session):
        return jsonify({'message': 'Stream already running', 'success': False})
    
    from youtube_live import start_stream
    result = start_stream()
    return jsonify({'message': 'Stream started' if result else 'Failed to start', 'success': result})

@app.route('/api/stream/stop', methods=['POST'])
def api_stop_stream():
    config = load_config()
    session = config.get('session_name', 'youtube_live')
    
    if not get_session_status(session):
        return jsonify({'message': 'No stream running', 'success': False})
    
    stop_session(session)
    return jsonify({'message': 'Stream stopped', 'success': True})

@app.route('/api/stream/restart', methods=['POST'])
def api_restart_stream():
    config = load_config()
    session = config.get('session_name', 'youtube_live')
    
    if get_session_status(session):
        stop_session(session)
        time.sleep(2)
    
    from youtube_live import start_stream
    result = start_stream()
    return jsonify({'message': 'Stream restarted' if result else 'Failed', 'success': result})

@app.route('/api/stream/multi_start', methods=['POST'])
def api_multi_start():
    from youtube_live import start_multi_stream
    result = start_multi_stream()
    return jsonify({'message': 'Multi-stream started', 'success': result})

@app.route('/api/stream/multi_stop', methods=['POST'])
def api_multi_stop():
    from youtube_live import stop_multi_stream
    result = stop_multi_stream()
    return jsonify({'message': 'Multi-stream stopped', 'success': result})

@app.route('/api/sessions')
def api_sessions():
    return jsonify(get_all_sessions())

@app.route('/api/logs')
def api_logs():
    logs = get_recent_logs(limit=20)
    result = []
    for log in logs:
        result.extend(read_log_tail(log, 10))
    return jsonify(result[-50:])

@app.route('/api/logs/recent')
def api_recent_logs():
    logs = get_recent_logs(limit=3)
    result = []
    for log in logs:
        result.extend(read_log_tail(log, 5))
    return jsonify(result[-15:])

@app.route('/api/logs/clear', methods=['POST'])
def api_clear_logs():
    import shutil
    if DEFAULT_LOG_DIR.exists():
        for log in DEFAULT_LOG_DIR.glob('*.log'):
            log.unlink()
    return jsonify({'message': 'Logs cleared', 'success': True})

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
    return jsonify({'message': 'Auto-restart enabled', 'success': True})

@app.route('/api/auto_restart/disable', methods=['POST'])
def api_ar_disable():
    config = load_auto_restart_config()
    config['enabled'] = False
    save_auto_restart_config(config)
    return jsonify({'message': 'Auto-restart disabled', 'success': True})

@app.route('/api/restart', methods=['POST'])
def api_restart_all():
    from youtube_live import auto_restart_all_streams
    auto_restart_all_streams()
    return jsonify({'message': 'Restart triggered', 'success': True})

@app.route('/api/daemon/start', methods=['POST'])
def api_daemon_start():
    daemon_script = Path(__file__).parent / 'auto_restart_daemon.py'
    subprocess.run(['python3', str(daemon_script), 'start'], capture_output=True)
    return jsonify({'message': 'Daemon started', 'success': True})

@app.route('/api/daemon/stop', methods=['POST'])
def api_daemon_stop():
    daemon_script = Path(__file__).parent / 'auto_restart_daemon.py'
    subprocess.run(['python3', str(daemon_script), 'stop'], capture_output=True)
    return jsonify({'message': 'Daemon stopped', 'success': True})

@app.route('/api/daemon/status')
def api_daemon_status():
    daemon_script = Path(__file__).parent / 'auto_restart_daemon.py'
    result = subprocess.run(['python3', str(daemon_script), 'status'], capture_output=True, text=True)
    running = 'running' in result.stdout.lower() or 'running' in result.stderr.lower()
    return jsonify({'running': running, 'output': result.stdout})

@app.route('/api/system/stats')
def api_system_stats():
    stats = get_system_stats()
    stats['ffmpeg_count'] = get_ffmpeg_process_count()
    return jsonify(stats)

@app.route('/api/system/check')
def api_system_check():
    all_installed, missing = check_dependencies()
    return jsonify({'all_installed': all_installed, 'missing': missing})

# ==================== Main ====================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='YouTube Live Web Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    args = parser.parse_args()
    
    print(f"Starting web dashboard on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
