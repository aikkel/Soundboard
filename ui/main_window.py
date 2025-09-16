import sys
import os
# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QStackedWidget, QGridLayout
)
from PyQt6.QtCore import Qt
from audio.sound_manager import SoundManager
from audio.mic_mixer import MicMixer  # Import the MicMixer class
from utils.config import load_settings, save_settings  # Import the config functions
from audio.audio_format_utils import decode_to_pcm  # Import the decode function
from utils.adjust_settings import apply_settings
import ui.settings_panel, ui.grids
from ui.play_panel import create_play_panel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundboard")
        self.setGeometry(100, 100, 800, 400)

        # Load settings
        self.settings = load_settings()
        print("Loaded settings:", self.settings)  # Debugging

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.scene0 = create_play_panel(self)
        self.scene1 = ui.settings_panel.create_scene1(self)

        self.central_widget.addWidget(self.scene0)
        self.central_widget.addWidget(self.scene1)

        self.sound_manager = SoundManager()
        self.mic_mixer = None  # Initialize the mic mixer as None

        # Apply loaded settings
        apply_settings(self)

    def test_mic(self):
        """Run the testMik script."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio", "testMik.py")
        os.system(f"python \"{script_path}\"")  # Use the full path to the script

    def save_and_return_to_scene0(self):
        """Save settings and return to Scene 0."""
        # Save current settings
        self.settings["mic_volume"] = self.dial_mc.value() / 100
        self.settings["speaker_volume"] = self.dial_sb.value() / 100
        self.settings["last_selected_mic"] = self.input_device.currentText()
        save_settings(self.settings)

        print("Settings saved:", self.settings)  # Debugging

        # Switch back to Scene 0
        self.central_widget.setCurrentWidget(self.scene0)

    def play_selected_sound(self, file_path):
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return

        # Ensure the MicMixer is instantiated
        if not self.mic_mixer:
            selected_device = self.input_device.currentData()
            self.mic_mixer = MicMixer(audio_device=selected_device)
            print(f"MicMixer initialized with device: {selected_device.description()}")

        # Decode file to PCM and load into mic_mixer
        pcm_bytes = decode_to_pcm(file_path)
        if pcm_bytes is not None and len(pcm_bytes) > 0:
            print(f"Loading PCM data of size {len(pcm_bytes)} bytes into MicMixer.")
            self.mic_mixer.load_sound(pcm_bytes)
        else:
            print("Failed to decode sound file to PCM.")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())