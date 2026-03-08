# YouTube Live Streaming Manager

Sistem otomatis untuk mengelola live streaming YouTube dengan FFmpeg, mendukung **multi-streaming** ke berbagai platform sekaligus.

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 Fitur

- ✅ **Interactive CLI Menu** - Menu berbasis teks yang mudah digunakan
- ✅ **Multi-Streaming** - Stream ke YouTube, Facebook, Twitch, TikTok sekaligus
- ✅ **Setup Otomatis** - Install semua dependencies dengan satu perintah
- ✅ **Easy Configuration** - Simpan Stream Key dan konfigurasi dalam file JSON
- ✅ **One-Click Streaming** - Mulai live streaming dengan command sederhana
- ✅ **Real-time Monitoring** - Dashboard monitoring dengan update langsung
- ✅ **Session Management** - Kelola sesi streaming dengan tmux
- ✅ **Google Drive Download** - Download video langsung dari Google Drive
- ✅ **Logging** - Semua aktivitas tercatat dalam file log
- ✅ **Duration Limit** - Atur durasi streaming (misal: 10 jam)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone atau download repository ini
cd /path/to/VPSLIVEYT

# Jalankan installation script
sudo ./install.sh
```

### 2. Gunakan Interactive CLI Menu (RECOMMENDED)

```bash
# Jalankan menu interaktif
python3 youtube_live.py menu
# atau
python3 cli_menu.py
```

Dari menu, Anda bisa:
- Setup konfigurasi
- Start/stop streaming
- Setup multi-streaming
- Monitor status
- Download dari Google Drive

### 3. Setup Konfigurasi (Manual)

```bash
# Setup dengan stream key
python3 youtube_live.py setup -k YOUR_YOUTUBE_STREAM_KEY

# Atau setup interaktif
python3 youtube_live.py setup
```

### 4. Mulai Streaming

```bash
# Single stream (continuous looping)
python3 youtube_live.py start

# Streaming dengan durasi (misal 10 jam)
python3 youtube_live.py start -d 10

# Multi-stream ke semua platform yang dikonfigurasi
python3 youtube_live.py multi-start
```

### 5. Monitor

```bash
# Cek status
python3 youtube_live.py status

# Monitor real-time (simple)
python3 youtube_live.py monitor

# Monitor dengan dashboard interaktif
python3 monitor.py -i
```

---

## 📖 Command Reference

### youtube_live.py

| Command | Deskripsi |
|---------|-----------|
| `menu` | **Interactive CLI menu** (recommended!) |
| `setup` | Setup konfigurasi (stream key, video path, session name) |
| `start` | Mulai single live streaming |
| `stop` | Stop live streaming |
| `status` | Tampilkan status lengkap |
| `monitor` | Monitor real-time simple |
| `download` | Download video dari Google Drive |
| `list` | List semua tmux sessions |
| `check` | Cek dependencies |
| `multi-start` | Start multi-streaming ke semua platform |
| `multi-stop` | Stop semua multi-streams |
| `auto-restart` | Setup auto-restart configuration |
| `auto-restart-now` | Restart semua streams sekarang |
| `auto-restart-daemon` | Jalankan daemon auto-restart |

### cli_menu.py - Interactive Menu

Menu interaktif dengan opsi:
- 📋 **Setup Configuration** - Set stream key, video path, session name
- 🔴 **Start Single Stream** - Mulai streaming tunggal
- 📡 **Multi-Streaming** - Setup & manage multi-platform streaming
- 📊 **Status** - Lihat status semua streams
- 🔍 **Monitor** - Real-time monitoring
- ⏹️ **Stop Streaming** - Stop stream
- 📥 **Download** - Download dari Google Drive
- 🛠️ **Tools** - Utilities & system info

### Options

| Option | Deskripsi |
|--------|-----------|
| `-k, --stream-key` | YouTube Stream Key |
| `-v, --video` | Path ke video file |
| `-n, --name` | Nama sesi tmux |
| `-d, --duration` | Durasi streaming (jam) |
| `-o, --output` | Output path untuk download |
| `--url` | URL Google Drive untuk download |

### Examples

```bash
# Setup konfigurasi
python3 youtube_live.py setup -k ABCD-1234-EFGH-5678

# Mulai streaming dengan video custom
python3 youtube_live.py start -v /home/user/myvideo.mp4

# Streaming 5 jam dengan session name custom
python3 youtube_live.py start -n MyStream -d 5

# Download dari Google Drive
python3 youtube_live.py download https://drive.google.com/uc?id=FILE_ID

# Download dengan nama file custom
python3 youtube_live.py download https://drive.google.com/uc?id=FILE_ID -o /root/live.mp4

# Multi-streaming
python3 youtube_live.py multi-start
python3 youtube_live.py multi-stop

# Interactive menu
python3 youtube_live.py menu
```

### monitor.py

| Option | Deskripsi |
|--------|-----------|
| `-i, --interactive` | Mode interaktif dengan keyboard shortcuts |
| `-n, --name` | Session name untuk monitor |

### Interactive Mode Shortcuts

| Key | Action |
|-----|--------|
| `S` | Start streaming |
| `R` | Restart streaming |
| `L` | View full logs |
| `C` | Clear screen |
| `Q` | Quit monitor |

---

## 📁 Struktur File

```
VPSLIVEYT/
├── youtube_live.py      # Main script untuk manage streaming
├── cli_menu.py          # Interactive CLI menu
├── monitor.py           # Dashboard monitoring
├── install.sh           # Installation script
├── config.template.json # Template konfigurasi
├── README.md            # Dokumentasi
└── .gitignore          # Git ignore rules
```

### Config File Location

Konfigurasi disimpan di: `~/.youtube_live_config.json`

Format:
```json
{
  "stream_key": "YOUR_STREAM_KEY",
  "video_path": "/root/live.mp4",
  "session_name": "youtube_live"
}
```

### Multi-Stream Config Location

Multi-stream konfigurasi disimpan di: `~/.youtube_live_multi_config.json`

Format:
```json
{
  "streams": [
    {
      "platform": "youtube",
      "session_name": "youtube_multi_1",
      "stream_key": "YOUR_YT_KEY",
      "rtmp_url": "rtmp://a.rtmp.youtube.com/live2"
    },
    {
      "platform": "facebook",
      "session_name": "facebook_live",
      "stream_key": "YOUR_FB_KEY",
      "rtmp_url": "rtmps://live-api-s.facebook.com:443/rtmp"
    }
  ]
}
```

### Log File Location

Log disimpan di: `/var/log/youtube_live/`

---

## 🔧 Manual Installation

Jika tidak menggunakan `install.sh`:

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y ffmpeg tmux python3 python3-pip

# Install gdown
pip3 install gdown

# Create log directory
sudo mkdir -p /var/log/youtube_live
sudo chmod 755 /var/log/youtube_live

# Set executable
chmod +x youtube_live.py monitor.py
```

---

## 🎯 Cara Mendapatkan Stream Key YouTube

1. Buka [YouTube Studio](https://studio.youtube.com/)
2. Klik **Create** → **Go Live**
3. Di tab **Stream**, copy **Stream Key**
4. ⚠️ **PENTING**: Jangan share stream key Anda!

---

## 📡 Multi-Streaming Setup

Streaming ke multiple platform sekaligus (YouTube, Facebook, Twitch, TikTok, dll).

### Cara Setup via CLI Menu (Recommended)

```bash
python3 youtube_live.py menu
```

Pilih menu **3. Multi-Streaming**, lalu:
1. Add Stream untuk setiap platform
2. Masukkan Stream Key masing-masing
3. Start All Streams

### Supported Platforms

| Platform | RTMP URL |
|----------|----------|
| YouTube | `rtmp://a.rtmp.youtube.com/live2` |
| Facebook | `rtmps://live-api-s.facebook.com:443/rtmp` |
| Twitch | `rtmp://live.twitch.tv/app` |
| TikTok | `rtmp://push.tiktok.com/live` |
| Custom | Masukkan RTMP URL sendiri |

### Cara Manual

```bash
# Start semua multi-streams
python3 youtube_live.py multi-start

# Stop semua multi-streams
python3 youtube_live.py multi-stop
```

---

## ⏰ Auto-Restart Feature

Fitur auto-restart akan **restart streaming secara otomatis** setiap interval tertentu untuk menjaga kestabilan stream.

### Cara Setup

```bash
# Via interactive menu (recommended)
python3 youtube_live.py menu
# Pilih: 4. Auto-Restart

# Atau via command line
python3 youtube_live.py auto-restart
```

### Options

| Option | Deskripsi |
|--------|-----------|
| Enable | Aktifkan auto-restart dengan interval tertentu |
| Disable | Matikan auto-restart |
| Set Interval | Atur interval restart (default: 6 jam) |
| Restart Now | Restart semua streams manual |
| Start Daemon | Jalankan daemon di background |

### Contoh Penggunaan

```bash
# Enable auto-restart setiap 4 jam
python3 youtube_live.py auto-restart
# Pilih: 1 (Enable), lalu masukkan: 4

# Restart semua streams sekarang
python3 youtube_live.py auto-restart-now

# Jalankan daemon (background process)
python3 youtube_live.py auto-restart-daemon
```

### Mengapa Auto-Restart?

- 🔄 **Mencegah freeze** - Restart berkala mencegah stream freeze
- 🛠️ **Recover dari error** - Auto-recover jika ada koneksi terputus
- ⏱️ **Jadwal otomatis** - Set interval sesuai kebutuhan (rekomendasi: 4-8 jam)

---

## 🛠️ Troubleshooting

### "Stream Key belum diatur"
```bash
python3 youtube_live.py setup -k YOUR_STREAM_KEY
```

### "Video file tidak ditemukan"
Pastikan video ada di path yang benar:
```bash
ls -la /root/live.mp4
```

Atau gunakan video lain:
```bash
python3 youtube_live.py start -v /path/to/your/video.mp4
```

### "Dependencies missing"
```bash
sudo ./install.sh
# atau
python3 youtube_live.py check
```

### "Sesi sudah berjalan"
Stop sesi yang ada atau gunakan nama berbeda:
```bash
# Stop sesi existing
python3 youtube_live.py stop

# Atau gunakan nama session baru
python3 youtube_live.py start -n NewSession
```

### FFmpeg error / koneksi terputus
- Cek koneksi internet
- Pastikan Stream Key valid
- Cek log: `tail -f /var/log/youtube_live/*.log`

---

## 📊 Monitoring Dashboard

Dashboard monitoring menampilkan:
- 🟢 Status streaming (LIVE/OFFLINE)
- ⏱️ Uptime sesi
- 💻 CPU, Memory, Disk usage
- 🎬 Active FFmpeg processes
- 📋 Recent logs

---

## 🔐 Security Notes

- ⚠️ **Jangan commit** file konfigurasi (`~/.youtube_live_config.json`) ke Git
- ⚠️ **Jangan share** Stream Key YouTube Anda
- File `.gitignore` sudah dikonfigurasi untuk mencegah commit konfigurasi sensitif

---

## 📝 License

MIT License - Silakan digunakan dan dimodifikasi.

---

## 🤝 Support

Jika ada masalah atau pertanyaan, silakan buat issue di repository ini.

---

**Happy Streaming! 🎥🔴**
