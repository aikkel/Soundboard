from PyQt6.QtMultimedia import QMediaDevices, QAudioSource, QAudioSink, QAudio, QAudioFormat
from PyQt6.QtCore import QIODevice, QByteArray, QBuffer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel
import sys
import numpy as np

class MicTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Microphone-to-Speaker Test")

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Dropdown to select microphone
        self.mic_selector = QComboBox()
        self.mic_selector.addItems([device.description() for device in QMediaDevices.audioInputs()])
        self.layout.addWidget(QLabel("Select Microphone:"))
        self.layout.addWidget(self.mic_selector)

        # Start button
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        self.layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("Stop Test")
        self.stop_button.clicked.connect(self.stop_test)
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.stop_button)

        # Initialize audio components
        self.audio_source = None
        self.audio_sink = None
        self.io_device = None
        self.sink_device = None

        # Generate a simple sine wave for testing
        sample_rate = 44100
        duration = 2  # seconds
        frequency = 440  # Hz (A4 note)
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        wave = (0.5 * np.sin(2 * np.pi * frequency * t) * (2**15 - 1)).astype(np.int16)

        # Convert to QByteArray
        audio_data = QByteArray(wave.tobytes())
        self.buffer = QBuffer()
        self.buffer.setData(audio_data)
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)

    def start_test(self):
        """Start the microphone-to-speaker test."""
        selected_device_index = self.mic_selector.currentIndex()
        selected_device = QMediaDevices.audioInputs()[selected_device_index]

        # Get the preferred audio format
        audio_format = selected_device.preferredFormat()

        # Print audio format details
        print(f"Audio Format: {audio_format.sampleRate()} Hz, {audio_format.channelCount()} channels, {audio_format.sampleFormat()}")

        # Create an audio source (microphone) and sink (speakers)
        self.audio_source = QAudioSource(selected_device, audio_format)
        self.audio_sink = QAudioSink(QMediaDevices.defaultAudioOutput(), audio_format)

        # Start capturing audio from the microphone
        self.io_device = self.audio_source.start()
        if not isinstance(self.io_device, QIODevice):
            raise RuntimeError("Failed to start audio input. Ensure a valid QIODevice is provided.")

        # Start playing audio to the speakers
        self.sink_device = self.audio_sink.start()
        print(f"Sink device is valid: {self.sink_device is not None}")

        # Connect the readyRead signal to feed audio to the speakers
        self.io_device.readyRead.connect(self.feed_audio_to_speakers)

        # Update button states
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        print(f"Microphone-to-speaker test started with device: {selected_device.description()}")

    def feed_audio_to_speakers(self):
        """Feed captured audio data to the speakers."""
        if self.io_device and self.audio_source.state() == QAudio.State.ActiveState:
            data = self.io_device.readAll()  # Read available audio data
            print(f"Captured {len(data)} bytes of audio data.")  # Debugging
            if data:
                self.sink_device.write(data)  # Write data to the audio sink
            else:
                print("No audio data captured.")

    def stop_test(self):
        """Stop the microphone-to-speaker test."""
        if self.audio_source:
            self.audio_source.stop()
        if self.audio_sink:
            self.audio_sink.stop()
        self.io_device = None
        self.sink_device = None
        

        # Update button states
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        print("Microphone-to-speaker test stopped.")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mic_test = MicTest()
    mic_test.show()

    sys.exit(app.exec())