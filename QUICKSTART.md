# 🚀 JARVIS Quick Start Guide

Get JARVIS up and running in 5 minutes!

## Step 1: Install Dependencies

### Option A: Enhanced Version (Recommended)
```bash
pip install -r requirements_enhanced.txt
```

### Option B: Lightweight Version (No Computer Vision)
```bash
pip install -r requirements.txt
```

### Fix PyTorch Issues (Windows)
If you get DLL errors with PyTorch:
```bash
# Download and install Visual C++ Redistributables
# https://aka.ms/vs/17/release/vc_redist.x64.exe

# OR install CPU-only version
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## Step 2: Get API Key

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up / Log in
3. Create an API key
4. Copy the key

## Step 3: Configure Environment

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_key_here
```

Or use the helper:
```bash
python setup_helper.py --env
```

## Step 4: Run Diagnostics (Optional but Recommended)

```bash
python setup_helper.py --full
```

This checks:
- ✓ Python version
- ✓ Dependencies
- ✓ API keys
- ✓ Audio devices
- ✓ Groq connection
- ✓ Skills

## Step 5: Launch JARVIS!

### Enhanced Version (Voice + GUI)
```bash
python main_enhanced.py
```

### Text Mode (No Voice)
```bash
python main_enhanced.py --text
```

### Different Theme
```bash
python main_enhanced.py --theme ULTRON
```

## 🎮 Controls

### GUI Controls
- **Click anywhere**: Pause/Resume
- **ESC**: Close
- **SPACE**: Pause/Resume
- **H**: Hide to system tray

### Voice Commands
```
"Jarvis, what time is it?"
"Search for Python tutorials"
"Open Chrome"
"Set volume to 50"
"Show system status"
```

### Text Commands
Just type without "Jarvis" prefix:
```
what time is it
search for AI news
open vscode
```

## 🎨 Themes

Three built-in themes:
- **STARK** (Default): Cyan/Blue - Classic Iron Man
- **ULTRON**: Red - Menacing AI
- **VISION**: Gold - Sophisticated AI

Change theme:
```bash
python main_enhanced.py --theme VISION
```

## 🛠️ Troubleshooting

### "GROQ_API_KEY not found"
- Make sure `.env` file exists in project root
- Check the key is correct (no quotes needed)
- Run: `python setup_helper.py --api` to test

### "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### "PyAudio not found"
**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Voice not working
- Check microphone permissions
- Run: `python setup_helper.py --audio`
- Use text mode: `python main_enhanced.py --text`

### GUI not showing
- Try: `python main_enhanced.py --no-gui`
- Check PyQt6 installation
- Update graphics drivers

## 📚 Next Steps

1. **Explore Skills**: Check `skills/` directory
2. **Customize**: Edit `config.py` for settings
3. **Create Skills**: Add your own in `skills/`
4. **Read Docs**: See `README_ENHANCED.md`

## 💡 Pro Tips

1. **Faster Startup**: Disable unused skills in `config.py`
2. **Better Voice**: Adjust rate/volume in `config.py`
3. **Custom Theme**: Create your own in `gui/enhanced_app.py`
4. **Automation**: Use automation presets in `config.py`
5. **Hot Reload**: Edit skills while JARVIS is running!

## 🆘 Still Having Issues?

Run the diagnostic tool:
```bash
python setup_helper.py
```

Check the logs:
```bash
cat jarvis.log
```

## 🎯 Common Use Cases

### Morning Routine
```
"Jarvis, good morning"
"Show system status"
"Search for today's news"
"Open Chrome"
```

### Work Mode
```
"Open VSCode"
"Open Spotify"
"Set volume to 30"
"Search GitHub for Python projects"
```

### Quick Tasks
```
"What time is it?"
"Create file notes.txt with content Hello World"
"Search YouTube for Python tutorials"
"Get system information"
```

## 🚀 You're Ready!

JARVIS is now ready to assist you. Enjoy your AI companion!

---

**Need help?** Check `README_ENHANCED.md` for detailed documentation.
