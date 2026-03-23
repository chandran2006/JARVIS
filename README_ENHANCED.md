# JARVIS Advanced AI Assistant - Enhanced Edition

A next-generation, modular AI assistant with advanced features including conversation memory, hot-reload skills, enhanced GUI with themes, system monitoring, and intelligent automation.

## 🌟 What's New in Enhanced Edition

### 🧠 Advanced AI Engine
- **Conversation Memory**: Maintains context across interactions
- **Response Caching**: Faster responses for repeated queries
- **Intelligent Error Recovery**: Automatically handles and recovers from errors
- **Streaming Support**: Real-time response generation (ready for future use)
- **Tool Result Tracking**: Remembers recent actions for context

### 🔌 Enhanced Plugin System
- **Hot-Reload**: Update skills without restarting
- **Priority System**: Control skill execution order
- **Async Support**: Non-blocking skill execution
- **Dependency Management**: Automatic skill dependency resolution
- **Performance Tracking**: Monitor skill usage and performance
- **Enable/Disable**: Toggle skills on the fly

### 🎨 Advanced GUI
- **Multiple Themes**: STARK (cyan), ULTRON (red), VISION (gold)
- **Voice Visualizer**: Real-time audio activity display
- **System Tray**: Minimize to tray, quick controls
- **Status Bar**: Live system information
- **Enhanced Animations**: Smoother, more responsive visuals
- **Keyboard Shortcuts**: 
  - `ESC` - Close
  - `SPACE` - Pause/Resume
  - `H` - Hide to tray

### 🛠️ Smart Skills
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Smart Detection**: Automatically finds applications
- **Safety Checks**: Prevents dangerous operations
- **Automation Chains**: Create multi-step workflows
- **Search History**: Track and recall previous searches
- **System Monitoring**: CPU, memory, disk usage

## 🚀 Quick Start

### Installation

1. **Clone and Navigate**
   ```bash
   cd Project_JARVIS-main
   ```

2. **Install Dependencies**
   ```bash
   # For full features
   pip install -r requirements_enhanced.txt
   
   # For lightweight (no computer vision)
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_key_here" > .env
   ```

### Running JARVIS

**Standard Mode (Voice + GUI)**
```bash
python main_enhanced.py
```

**Text-Only Mode**
```bash
python main_enhanced.py --text
```

**Different Themes**
```bash
python main_enhanced.py --theme ULTRON  # Red theme
python main_enhanced.py --theme VISION  # Gold theme
```

**Voice Without GUI**
```bash
python main_enhanced.py --no-gui
```

## 💬 Usage Examples

### Basic Commands
```
"Jarvis, what time is it?"
"Search for Python tutorials"
"Open Chrome"
"Set volume to 50"
"Create a file called notes.txt with content Hello World"
```

### Advanced Commands
```
"Show system status"
"Get system information"
"Search YouTube for AI tutorials"
"Create automation called morning routine"
"Show search history"
"Clear history"
"Reload skills"
```

### Smart Features
- **Context Awareness**: "What did I just search for?"
- **Multi-Engine Search**: Specify Google, YouTube, GitHub, or StackOverflow
- **Automation**: Chain multiple commands together
- **Memory**: Remembers previous conversations

## 📁 Project Structure

```
Project_JARVIS-main/
├── core/
│   ├── engine.py              # Original engine
│   ├── enhanced_engine.py     # ✨ Advanced AI engine
│   ├── registry.py            # Original registry
│   ├── enhanced_registry.py   # ✨ Hot-reload plugin system
│   ├── skill.py               # Base skill class
│   └── voice.py               # Voice I/O
├── gui/
│   ├── app.py                 # Original GUI
│   └── enhanced_app.py        # ✨ Advanced GUI with themes
├── skills/
│   ├── smart_skills.py        # ✨ Enhanced smart skills
│   ├── system_ops.py          # System control
│   ├── web_ops.py             # Web operations
│   ├── memory_ops.py          # Memory management
│   ├── datetime_ops.py        # Date/time
│   ├── file_ops.py            # File operations
│   └── ...                    # Other skills
├── main.py                    # Original entry point
├── main_enhanced.py           # ✨ Enhanced entry point
├── requirements.txt           # Original dependencies
├── requirements_enhanced.txt  # ✨ Enhanced dependencies
└── .env                       # API keys
```

## 🎯 Key Features Comparison

| Feature | Original | Enhanced |
|---------|----------|----------|
| Conversation Memory | ❌ | ✅ |
| Response Caching | ❌ | ✅ |
| Hot-Reload Skills | ❌ | ✅ |
| Priority System | ❌ | ✅ |
| Multiple Themes | ❌ | ✅ (3 themes) |
| Voice Visualizer | ❌ | ✅ |
| System Tray | ❌ | ✅ |
| Status Bar | ❌ | ✅ |
| Cross-Platform | Partial | ✅ Full |
| System Monitoring | ❌ | ✅ |
| Search History | ❌ | ✅ |
| Automation Chains | ❌ | ✅ |
| Error Recovery | Basic | Advanced |
| Performance Tracking | ❌ | ✅ |

## 🔧 Configuration

### Environment Variables (.env)
```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_key  # Optional
```

### Skill Priority
Edit skills to set priority (higher = executed first):
```python
class MySkill(Skill):
    priority = 90  # High priority (default is 50)
```

### Theme Customization
Edit `gui/enhanced_app.py` to create custom themes:
```python
CUSTOM = {
    "primary": QColor("#YOUR_COLOR"),
    "accent": QColor("#YOUR_COLOR"),
    "bg": QColor("#000000"),
    "warning": QColor("#FFA500"),
    "success": QColor("#00FF00"),
    "error": QColor("#FF0000")
}
```

## 🛡️ Safety Features

- **Command Filtering**: Blocks dangerous system commands
- **File Size Limits**: Prevents reading huge files
- **Timeout Protection**: Commands timeout after 10 seconds
- **Safe Mode**: Optional safety checks for system commands
- **Sandboxed Execution**: Skills run in isolated context

## 🐛 Troubleshooting

### PyTorch DLL Error (Windows)
```bash
# Install Visual C++ Redistributables
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

# OR use CPU-only PyTorch
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Voice Recognition Not Working
```bash
# Install PyAudio dependencies
# Windows: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/
# macOS: brew install portaudio
# Linux: sudo apt-get install portaudio19-dev
```

### GUI Not Showing
```bash
# Ensure PyQt6 is installed
pip install --upgrade PyQt6

# Try without GUI
python main_enhanced.py --no-gui
```

## 📊 Performance Tips

1. **Disable Unused Skills**: Use `disable_skill()` for skills you don't need
2. **Adjust Cache Size**: Modify `ConversationManager.max_history`
3. **Use Text Mode**: Faster than voice mode for testing
4. **Disable Computer Vision**: Comment out ultralytics/torch if not needed

## 🔮 Future Enhancements

- [ ] Voice cloning for custom JARVIS voice
- [ ] Plugin marketplace for community skills
- [ ] Mobile companion app
- [ ] Multi-language support
- [ ] Cloud sync for memory/settings
- [ ] Advanced automation with conditionals
- [ ] Integration with smart home devices
- [ ] Real-time translation
- [ ] Sentiment analysis
- [ ] Proactive suggestions

## 🤝 Contributing

To create a new skill:

1. Create file in `skills/` directory
2. Inherit from `Skill` base class
3. Implement required methods
4. Set priority if needed
5. JARVIS will auto-load it!

Example:
```python
from core.skill import Skill

class MySkill(Skill):
    priority = 70  # Optional
    
    @property
    def name(self) -> str:
        return "my_skill"
    
    def get_tools(self):
        return [...]  # Tool definitions
    
    def get_functions(self):
        return {...}  # Function mappings
```

## 📝 License

MIT License - Feel free to modify and distribute!

## 🙏 Credits

- Built with [Groq](https://groq.com/) LLM API
- Inspired by Marvel's JARVIS
- GUI powered by PyQt6
- Voice by pyttsx3

---

**Made with ❤️ for the AI community**

*"Sometimes you gotta run before you can walk."* - Tony Stark
