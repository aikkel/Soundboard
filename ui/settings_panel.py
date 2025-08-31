import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import ( QWidget, QVBoxLayout, QPushButton, QLabel, QDial, QComboBox, QMessageBox )
from PyQt6.QtMultimedia import QMediaDevices
from utils.adjust_settings import load_sounds

# Scene 1: Settings Panel
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
        self.refresh_button.clicked.connect(lambda: load_sounds(self))
        layout.addWidget(self.refresh_button)

        # Rename and connect the Test Mic button
        self.test_mic_button = QPushButton("Test Mic")
        self.test_mic_button.clicked.connect(self.test_mic)  # Connect to the test_mic method
        layout.addWidget(self.test_mic_button)

        # self.stop_mic_button = QPushButton("Stop Mic Capture")
        # self.stop_mic_button.clicked.connect(self.stop_mic_capture)
        # layout.addWidget(self.stop_mic_button)

        # Save button: Save settings and return to Scene 0
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_and_return_to_scene0)
        layout.addWidget(self.save_button)

        # Discard button: Return to Scene 0 without saving
        self.discard_button = QPushButton("Discard")
        self.discard_button.clicked.connect(lambda: self.central_widget.setCurrentWidget(self.scene0))
        layout.addWidget(self.discard_button)


        # Add Legal Information button
        self.legal_button = QPushButton("Legal Information")
        self.legal_button.clicked.connect(lambda: show_legal_info(self))
        layout.addWidget(self.legal_button)

        scene.setLayout(layout)
        return scene

def show_legal_info(self):
        """Display legal information about VB-Cable and ffmpeg."""

        legal_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legal.txt")

        try:
            with open(legal_file, "r", encoding="utf-8") as f:
                legal_text = f.read()
        except FileNotFoundError:
            legal_text = "Legal information file not found. Please make sure 'legal.txt' exists."

        QMessageBox.information(
            self,
            "Legal Information",
            legal_text,
            QMessageBox.StandardButton.Ok
        )