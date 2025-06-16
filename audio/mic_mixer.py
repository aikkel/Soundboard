from PyQt6.QtMultimedia import QAudioSource, QAudioSink, QMediaDevices, QAudioFormat
from PyQt6.QtCore import QIODevice, QTimer, QByteArray
import numpy as np

class MicMixer:
    def __init__(self, audio_device=None, output_device=None):
        self.audio_device = audio_device or QMediaDevices.defaultAudioInput()
        self.output_device = output_device or self.get_vbcable_output_device()

        if not self.audio_device:
            raise RuntimeError("No microphone device found.")
        else:
            print(f"Using audio input device: {self.audio_device.description()}")

        if not self.output_device:
            print("Warning: VB Cable not found. Using default audio output.")
            self.output_device = QMediaDevices.defaultAudioOutput()

        self.input_stream = None
        self.output_stream = None
        self.sound_buffer = None

        self.init_audio_streams()

    def init_audio_streams(self):
        self.audio_input = QAudioSource(self.audio_device)
        self.audio_output = QAudioSink(self.output_device)

        self.input_stream = self.audio_input.start()
        if self.input_stream is None:
            print(f"Failed to initialize input_stream for device: {self.audio_device.description()}")
            print("Try selecting a different input device or check your microphone permissions.")
            return  # or raise an exception
        self.output_stream = self.audio_output.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.mix_audio)
        self.timer.start(10)

    def load_sound(self, sound_data):
        self.sound_buffer = sound_data

    def mix_audio(self):
        if self.input_stream is None:
            print("Input stream is not initialized.")
            return
        mic_data = self.input_stream.readAll()
        if not mic_data:
            return

        mic_array = np.frombuffer(mic_data, dtype=np.int16)
        sound_array = np.frombuffer(self.sound_buffer, dtype=np.int16)

        # Ensure sound array length matches mic data length
        if len(sound_array) < len(mic_array):
            sound_array = np.pad(sound_array, (0, len(mic_array) - len(sound_array)), mode='constant')

        mixed_array = np.add(mic_array, sound_array[:len(mic_array)], dtype=np.int16)
        mixed_data = mixed_array.tobytes()

        self.output_stream.write(mixed_data)

    def get_vbcable_output_device(self):
        devices = QMediaDevices.audioOutputs()
        for device in devices:
            if "VB-Audio" in device.description():
                return device
        return None

print("Available input devices:")
for dev in QMediaDevices.audioInputs():
    print(dev.description())
