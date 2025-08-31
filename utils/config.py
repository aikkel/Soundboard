import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

# Default settings fallback
DEFAULT_SETTINGS = {
    "mic_volume": 1.00,
    "speaker_volume": 1.00,
    "last_selected_mic": None,
    "last_sound_folder": None
}

def load_settings():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Warning: settings.json is corrupted. Loading defaults.")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings, f, indent=4)