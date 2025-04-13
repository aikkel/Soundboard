import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QStackedWidget, QGridLayout, QDial, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaDevices  # Add this import
import sys
import os
from audio.sound_manager import SoundManager
from audio.mic_mixer import MicMixer  # Import the MicMixer class
from config import load_settings, save_settings  # Import the config functions

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

        self.scene0 = self.create_scene0()
        self.scene1 = self.create_scene1()

        self.central_widget.addWidget(self.scene0)
        self.central_widget.addWidget(self.scene1)

        self.sound_manager = SoundManager()
        self.mic_mixer = None  # Initialize the mic mixer as None

        # Apply loaded settings
        self.apply_settings()

    def create_scene0(self):
        scene = QWidget()
        self.layout = QVBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.layout.addWidget(self.search_bar)
        
        # Add a grid layout for the file grid
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)
        
        # Placeholder label for the grid
        placeholder_label = QLabel("No files loaded. Connect a folder to populate.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(placeholder_label, 0, 0, 1, 4)  # Spanning 4 columns
        
        # Add a Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_grid)
        self.layout.addWidget(self.refresh_button)
        
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.scene1))
        self.layout.addWidget(self.settings_button)
        
        scene.setLayout(self.layout)
        return scene

    def refresh_grid(self):
        # Placeholder functionality for refreshing the grid
        # This can be extended to reload the folder or update the grid dynamically
        print("Refresh button clicked")
    
    def load_sounds(self):
        """Open a folder dialog to select a sound folder and populate the grid."""
        folder = QFileDialog.getExistingDirectory(self, "Select Sound Folder")
        if folder:
            self.settings["last_sound_folder"] = folder  # Save the selected folder to settings
            save_settings(self.settings)  # Persist the updated settings
            print(f"Selected folder saved: {folder}")  # Debugging
            self.populate_sound_buttons(folder)
    
    def populate_sound_buttons(self, folder):
        # Clear existing buttons in the grid
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Get a list of sound files in the folder
        sound_files = [f for f in os.listdir(folder) if f.endswith(('.mp3', '.wav', '.ogg'))]
        
        row, col = 0, 0
        for sound in sound_files:
            file_path = os.path.join(folder, sound)  # Full path to the sound file
            btn = QPushButton(sound)
            btn.clicked.connect(lambda checked, path=file_path: self.play_selected_sound(path))  # Connect button to playback
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
    
    def create_scene1(self):
        scene = QWidget()
        layout = QVBoxLayout()

        # Populate the microphone input device list
        self.input_device = QComboBox()
        audio_devices = QMediaDevices.audioInputs()
        for device in audio_devices:
            self.input_device.addItem(device.description(), device)
        layout.addWidget(QLabel("Microphone Input:"))
        layout.addWidget(self.input_device)

        self.output_device = QComboBox()
        self.output_device.addItems(["Speaker 1", "Speaker 2"])
        layout.addWidget(QLabel("Microphone Output:"))
        layout.addWidget(self.output_device)

        self.dial_mc = QDial()
        self.dial_mc.setValue(65)
        layout.addWidget(QLabel("Microphone Volume"))
        layout.addWidget(self.dial_mc)

        self.dial_sb = QDial()
        self.dial_sb.setValue(65)
        layout.addWidget(QLabel("Speaker Volume"))
        layout.addWidget(self.dial_sb)

        self.refresh_button = QPushButton("Select Folder")
        self.refresh_button.clicked.connect(self.load_sounds)
        layout.addWidget(self.refresh_button)

        # Rename and connect the Test Mic button
        self.test_mic_button = QPushButton("Test Mic")
        self.test_mic_button.clicked.connect(self.test_mic)  # Connect to the test_mic method
        layout.addWidget(self.test_mic_button)

        self.stop_mic_button = QPushButton("Stop Mic Capture")
        self.stop_mic_button.clicked.connect(self.stop_mic_capture)
        layout.addWidget(self.stop_mic_button)

        # Save button: Save settings and return to Scene 0
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_and_return_to_scene0)
        layout.addWidget(self.save_button)

        # Discard button: Return to Scene 0 without saving
        self.discard_button = QPushButton("Discard")
        self.discard_button.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.scene0))
        layout.addWidget(self.discard_button)

        scene.setLayout(layout)
        return scene

    def test_mic(self):
        """Run the testMik script."""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio", "testMik.py")
        os.system(f"python \"{script_path}\"")  # Use the full path to the script

    def apply_settings(self):
        """Apply settings to the UI components."""
        print("Applying settings...")  # Debugging
        self.dial_mc.setValue(int(self.settings.get("mic_volume", 1.00) * 100))
        self.dial_sb.setValue(int(self.settings.get("speaker_volume", 1.00) * 100))
        last_selected_mic = self.settings.get("last_selected_mic")
        if last_selected_mic:
            index = self.input_device.findText(last_selected_mic)
            if index != -1:
                self.input_device.setCurrentIndex(index)

        # Load the last selected folder and populate the grid
        last_folder = self.settings.get("last_sound_folder")
        if last_folder and os.path.exists(last_folder):
            print(f"Loading sounds from last folder: {last_folder}")  # Debugging
            self.populate_sound_buttons(last_folder)
        else:
            print("No valid folder found in settings.")  # Debugging

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
        if self.sound_manager.is_playing():
            print(f"Stopping sound: {file_path}")  # Debugging
            self.sound_manager.stop_sound()
        else:
            print(f"Playing sound: {file_path}")  # Debugging
            self.sound_manager.play_sound(file_path)

    def start_mic_capture(self):
        """Start capturing audio from the microphone."""
        if not self.mic_mixer:
            selected_device = self.input_device.currentData()  # Get the selected QAudioDevice
            self.mic_mixer = MicMixer(audio_device=selected_device)  # Pass the selected device
            print(f"Microphone capture started with device: {selected_device.description()}")
        else:
            print("Microphone is already capturing.")

    def stop_mic_capture(self):
        """Stop capturing audio from the microphone."""
        if self.mic_mixer:
            self.mic_mixer.stop_capture()  # Stop the mic mixer
            self.mic_mixer = None  # Reset the mic mixer
            print("Microphone capture stopped.")
        else:
            print("Microphone is not capturing.")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())