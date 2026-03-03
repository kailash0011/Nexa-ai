# 🤖 Nexa — Your Personal AI Assistant

```
  _   _ _______  _____ ___
 | \ | | ____\ \/ /  _  \
 |  \| |  _|  \  /| |_| |
 | |\  | |___ /  \|  _  /
 |_| \_|_____/_/\_\_| \_\

  Your Personal AI Assistant — 100% FREE
```

Nexa is a **100% free, open-source personal AI assistant** for Kailash (and anyone who sets it up!) that runs 24/7 on your PC. Nexa can control your computer, make phone calls, send WhatsApp & Messenger messages, set reminders, monitor your system, and communicate on your behalf when you're busy.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI Brain** | Local LLM via Ollama (Phi-3) — no cloud, no cost |
| 🎙️ **Voice Control** | Say "Hey Nexa" to issue commands hands-free |
| 🔊 **Text-to-Speech** | Nexa speaks responses aloud via pyttsx3 |
| 📞 **Phone Calls** | Dial & hang up via ADB (Android Debug Bridge) |
| 💬 **WhatsApp** | Send messages via pywhatkit & WhatsApp Web |
| 📱 **Messenger** | Send Facebook Messenger messages via Selenium |
| 🗂️ **File Manager** | Search, open, and inspect files on your PC |
| 🚀 **App Launcher** | Open & close Windows/Linux/macOS applications |
| 🖥️ **System Monitor** | Real-time CPU, RAM, disk, and battery status |
| ⏰ **Scheduler** | Set reminders and timers that fire in the background |
| 📒 **Contacts** | JSON-based contact book with fuzzy search |
| 🔕 **Busy Mode** | Auto-reply on your behalf when you're unavailable |

---

## 🛠️ Tech Stack (All FREE!)

- **Python 3.11+**
- **[Ollama](https://ollama.ai)** — local LLM server (runs Phi-3 on your GPU/CPU)
- **pyttsx3** — offline text-to-speech
- **SpeechRecognition** — speech-to-text via Google's free Web Speech API
- **pywhatkit** — WhatsApp Web automation
- **Selenium + webdriver-manager** — browser automation for Messenger
- **psutil** — system monitoring
- **schedule** — task scheduling
- **python-dotenv** — environment variable management
- **ADB (Android Debug Bridge)** — phone call / SMS control

---

## 📋 Prerequisites

1. **Python 3.11+** — [Download](https://www.python.org/downloads/)
2. **Ollama** — [Install](https://ollama.ai) and pull the Phi-3 model:
   ```bash
   ollama pull phi3
   ollama serve   # keep this running in the background
   ```
3. **ADB** (optional, for phone calls):
   - [Download Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)
   - Enable USB Debugging on your Android phone
   - Connect phone via USB
4. **Google Chrome** (for Messenger automation via Selenium)
5. **Microphone** (optional, for voice input)

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/kailash0011/Nexa-ai.git
cd Nexa-ai

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure Nexa
cp .env.example .env
# Edit .env with your settings (see Configuration section below)
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and edit:

```env
OWNER_NAME=Kailash          # Your name — Nexa uses this everywhere
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=phi3

# Optional free API fallbacks (if Ollama is unavailable)
GEMINI_API_KEY=             # Google Gemini free API key
GROQ_API_KEY=               # Groq free API key

BUSY_MODE=false             # Start in busy/auto-reply mode?
VOICE_ENABLED=true          # Enable TTS and microphone input
VOICE_SPEED=150             # Words per minute (100–200)
VOICE_GENDER=female         # "male" or "female"
ADB_ENABLED=true            # Enable phone features via ADB
```

---

## ▶️ Usage

```bash
# Start Nexa (auto-detects voice / text mode)
python main.py

# Force text-only mode (no microphone needed)
python main.py --text
```

### Example Commands

```
You: Call Ram and tell him my boss is busy
🤖 Nexa: 📞 Calling Ram… and sent a message: 'my boss is busy'

You: Send WhatsApp to Sandhya - I will call you later
🤖 Nexa: ✅ WhatsApp message sent to Sandhya: 'I will call you later'

You: I'm busy for 2 hours
🤖 Nexa: 🔕 Busy mode ON for 2 hours. I'll handle your messages!

You: Open Chrome
🤖 Nexa: 🚀 Opening Chrome… ✅

You: What's my system status?
🤖 Nexa: 🖥️ CPU: 23.0% | RAM: 8.1/16.0 GB (51%) | Disk: 234 GB free of 500 GB | Battery: 78% (🔋 on battery)

You: Remind me to take a break in 30 minutes
🤖 Nexa: ⏰ Reminder set: 'take a break' — I'll remind you in 30 minutes

You: Search for report.pdf
🤖 Nexa: 🔍 Found 2 file(s) matching 'report.pdf'

You: Bye Nexa
🤖 Nexa: Goodbye Kailash! I'll be here when you need me. 👋
```

---

## 📁 Project Structure

```
nexa-ai/
├── main.py                        # Entry point
├── config.py                      # Configuration loader
├── .env.example                   # Example environment variables
├── requirements.txt               # Python dependencies
├── README.md                      # This file
│
├── nexa/
│   ├── assistant.py               # Main NexaAssistant orchestrator
│   ├── brain/
│   │   ├── llm.py                 # LLM (Ollama/Gemini/Groq)
│   │   ├── intent_parser.py       # Natural language → structured actions
│   │   └── auto_reply.py          # Smart busy-mode auto-replies
│   ├── voice/
│   │   ├── speaker.py             # pyttsx3 text-to-speech
│   │   └── listener.py            # SpeechRecognition microphone input
│   ├── integrations/
│   │   ├── phone_call.py          # ADB phone calls & SMS
│   │   ├── whatsapp.py            # pywhatkit WhatsApp messages
│   │   └── messenger.py           # Selenium Messenger automation
│   ├── services/
│   │   ├── file_manager.py        # File search, open, list
│   │   ├── app_launcher.py        # Open/close desktop apps
│   │   ├── system_monitor.py      # CPU/RAM/disk/battery monitoring
│   │   └── scheduler.py           # Reminder & timer scheduling
│   ├── contacts/
│   │   ├── manager.py             # Contact CRUD with fuzzy search
│   │   └── contacts.json          # Contact storage
│   └── utils/
│       └── logger.py              # Colored console + file logging
│
└── tests/
    ├── test_brain.py
    ├── test_voice.py
    ├── test_services.py
    └── test_contacts.py
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Credits

Built with ❤️ for **Kailash** using:
- [Ollama](https://ollama.ai) — local AI inference
- [Microsoft Phi-3](https://azure.microsoft.com/en-us/blog/introducing-phi-3/) — the AI model
- [pyttsx3](https://pyttsx3.readthedocs.io/) — offline TTS
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) — voice input
- [pywhatkit](https://pypi.org/project/pywhatkit/) — WhatsApp automation
- [Selenium](https://selenium.dev) — browser automation
- [psutil](https://psutil.readthedocs.io/) — system monitoring
