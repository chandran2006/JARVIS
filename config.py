"""
JARVIS Configuration File
Customize your JARVIS experience here
"""

# ============================================================================
# AI ENGINE SETTINGS
# ============================================================================

AI_CONFIG = {
    # Groq Model Selection
    "model": "llama-3.3-70b-versatile",  # Options: llama-3.3-70b-versatile, mixtral-8x7b-32768
    
    # Conversation Settings
    "max_history": 10,  # Number of conversation turns to remember
    "max_tokens": 500,  # Maximum response length
    "temperature": 0.7,  # Creativity (0.0-1.0, higher = more creative)
    
    # Cache Settings
    "cache_enabled": True,
    "cache_timeout": 300,  # Seconds (5 minutes)
    
    # Response Settings
    "streaming": False,  # Enable streaming responses (future feature)
    "timeout": 30,  # API timeout in seconds
}

# ============================================================================
# VOICE SETTINGS
# ============================================================================

VOICE_CONFIG = {
    # Speech Recognition
    "recognition_timeout": 5,  # Seconds to wait for speech
    "pause_threshold": 0.8,  # Pause detection sensitivity
    "ambient_noise_duration": 1,  # Seconds to adjust for noise
    
    # Text-to-Speech
    "rate": 175,  # Speaking speed (words per minute)
    "volume": 0.9,  # Volume (0.0-1.0)
    "voice_preference": "male",  # Preferred voice gender
    
    # Wake Words
    "wake_words": ["jarvis", "hey jarvis", "ok jarvis"],
    
    # Direct Command Keywords (no wake word needed)
    "direct_commands": [
        "open", "search", "create", "set", "get", "show", 
        "tell", "what", "who", "when", "where", "how", "why"
    ],
}

# ============================================================================
# GUI SETTINGS
# ============================================================================

GUI_CONFIG = {
    # Window Settings
    "width": 1200,
    "height": 700,
    "frameless": True,
    "transparent_bg": True,
    
    # Theme
    "default_theme": "STARK",  # Options: STARK, ULTRON, VISION
    
    # Animation Settings
    "animation_speed": 30,  # FPS
    "enable_glow": True,
    "enable_pulse": True,
    
    # System Tray
    "minimize_to_tray": True,
    "start_minimized": False,
    
    # Voice Visualizer
    "visualizer_bars": 32,
    "visualizer_enabled": True,
}

# ============================================================================
# SKILL SETTINGS
# ============================================================================

SKILL_CONFIG = {
    # Auto-reload
    "hot_reload": True,
    "reload_check_interval": 5,  # Seconds
    
    # Safety
    "safe_mode": True,  # Enable safety checks for dangerous operations
    "file_size_limit": 1048576,  # 1MB max file read size
    "command_timeout": 10,  # Seconds for system commands
    
    # Performance
    "async_execution": True,
    "parallel_tools": False,  # Execute multiple tools in parallel (experimental)
    
    # Disabled Skills (add skill names to disable)
    "disabled_skills": [
        # "detection_skill",  # Uncomment to disable computer vision
        # "whatsapp_skill",   # Uncomment to disable WhatsApp
    ],
}

# ============================================================================
# SYSTEM SETTINGS
# ============================================================================

SYSTEM_CONFIG = {
    # Logging
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "log_to_file": True,
    "log_file": "jarvis.log",
    
    # Performance
    "enable_profiling": False,  # Track performance metrics
    "memory_limit": 512,  # MB (soft limit)
    
    # Security
    "require_confirmation": False,  # Ask before executing dangerous commands
    "encrypted_storage": False,  # Encrypt memory storage (requires cryptography)
    
    # Updates
    "check_for_updates": True,
    "auto_update_skills": False,
}

# ============================================================================
# CUSTOM THEME DEFINITION
# ============================================================================

CUSTOM_THEMES = {
    "MATRIX": {
        "primary": "#00FF00",
        "accent": "#00AA00",
        "bg": "#000000",
        "warning": "#FFFF00",
        "success": "#00FF00",
        "error": "#FF0000"
    },
    "CYBERPUNK": {
        "primary": "#FF00FF",
        "accent": "#00FFFF",
        "bg": "#0A0A0A",
        "warning": "#FFFF00",
        "success": "#00FF00",
        "error": "#FF0000"
    },
    "STEALTH": {
        "primary": "#808080",
        "accent": "#C0C0C0",
        "bg": "#000000",
        "warning": "#FFA500",
        "success": "#00FF00",
        "error": "#FF0000"
    }
}

# ============================================================================
# AUTOMATION PRESETS
# ============================================================================

AUTOMATION_PRESETS = {
    "morning_routine": [
        "get system information",
        "open chrome",
        "search for news"
    ],
    "work_mode": [
        "open vscode",
        "open spotify",
        "set volume to 30"
    ],
    "shutdown_routine": [
        "show stats",
        "clear history"
    ]
}

# ============================================================================
# API KEYS (Use .env file instead for security)
# ============================================================================

# DO NOT store API keys here in production!
# Use .env file instead:
# GROQ_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here

API_KEYS = {
    # Only use for development/testing
    # "GROQ_API_KEY": "your_key_here",
}

# ============================================================================
# EXPERIMENTAL FEATURES
# ============================================================================

EXPERIMENTAL = {
    "voice_cloning": False,  # Custom voice (requires additional setup)
    "emotion_detection": False,  # Detect user emotion from voice
    "proactive_suggestions": False,  # JARVIS suggests actions
    "learning_mode": False,  # Learn from user patterns
    "multi_language": False,  # Support multiple languages
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config(section: str) -> dict:
    """Get configuration for a specific section."""
    configs = {
        "ai": AI_CONFIG,
        "voice": VOICE_CONFIG,
        "gui": GUI_CONFIG,
        "skill": SKILL_CONFIG,
        "system": SYSTEM_CONFIG,
    }
    return configs.get(section, {})

def update_config(section: str, key: str, value):
    """Update a configuration value."""
    configs = {
        "ai": AI_CONFIG,
        "voice": VOICE_CONFIG,
        "gui": GUI_CONFIG,
        "skill": SKILL_CONFIG,
        "system": SYSTEM_CONFIG,
    }
    if section in configs and key in configs[section]:
        configs[section][key] = value
        return True
    return False
