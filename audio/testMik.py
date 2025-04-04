import sys
import threading
import pyaudio
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QLabel

class AudioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyAudio Mic-to-Speaker Test")

        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.running = False
        self.stream_thread = None

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Input device dropdown
        self.device_selector = QComboBox()
        self.devices = self.get_input_devices()
        for name in self.devices:
            self.device_selector.addItem(name)
        self.layout.addWidget(QLabel("Select Microphone:"))
        self.layout.addWidget(self.device_selector)

        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_audio)
        self.layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_audio)
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.stop_button)

    def get_input_devices(self):
        device_names = {}
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)

            if dev['maxInputChannels'] > 0:
                name = dev['name']
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="replace")
                device_names[name] = i
        return device_names

    def start_audio(self):
        index = self.device_selector.currentIndex()
        device_name = self.device_selector.currentText()
        device_index = self.devices[device_name]

        self.running = True
        self.stream_thread = threading.Thread(target=self.run_audio, args=(device_index,))
        self.stream_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        print(f"🎙️ Using device: {device_name}")

    def run_audio(self, device_index):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 48000
        CHUNK = 1024

        stream_in = self.p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                input_device_index=device_index,
                                frames_per_buffer=CHUNK)

        stream_out = self.p.open(format=FORMAT,
                                 channels=CHANNELS,
                                 rate=RATE,
                                 output=True,
                                 frames_per_buffer=CHUNK)

        print("🔁 Mic passthrough started")
        while self.running:
            try:
                data = stream_in.read(CHUNK, exception_on_overflow=False)
                stream_out.write(data)
            except Exception as e:
                print(f"⚠️ Audio error: {e}")
                break

        stream_in.stop_stream()
        stream_in.close()
        stream_out.stop_stream()
        stream_out.close()
        print("🛑 Mic passthrough stopped")

    def stop_audio(self):
        self.running = False
        if self.stream_thread:
            self.stream_thread.join()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        self.stop_audio()
        self.p.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioApp()
    window.show()
    sys.exit(app.exec())
