from PyQt6.QtMultimedia import QAudioSource, QMediaDevices, QAudioFormat
from PyQt6.QtCore import QIODevice
from audio.audio_format_utils import audio_matches_qt_format

class MicMixer:
    def __init__(self, audio_device=None):
        self.audio_device = audio_device or QMediaDevices.defaultAudioInput()
        if not self.audio_device:
            raise RuntimeError("No audio input device found.")

        # Get the preferred audio format for the selected device
        self.audio_format = self.audio_device.preferredFormat()

        # Create an audio source (captures mic audio)
        self.audio_source = QAudioSource(self.audio_device, self.audio_format)

        # Create a buffer to store audio data
        self.audio_buffer = bytearray()

        # Start capturing audio and get the IO device
        self.io_device = self.audio_source.start()
        if not isinstance(self.io_device, QIODevice):
            raise RuntimeError("Failed to start audio input. Ensure a valid QIODevice is provided.")

        # Connect the readyRead signal to capture audio data
        self.io_device.readyRead.connect(self.capture_audio)

        # Set the default microphone volume (scale 0.0 - 1.0)
        self.volume = 0.65
        self.audio_source.setVolume(self.volume)

    def capture_audio(self):
        """Capture audio data from the microphone."""
        from PyQt6.QtMultimedia import QAudio  # Import QAudio for state constants
        if self.io_device and self.audio_source.state() == QAudio.State.ActiveState:
            data = self.io_device.readAll()  # Read available audio data
            self.audio_buffer.extend(data)  # Append data to the buffer
            print(f"Captured {len(data)} bytes of audio data.")

    def stop_capture(self):
        """Stop capturing audio."""
        if self.audio_source:
            self.audio_source.stop()  # Stop the audio source
            self.io_device = None  # Clear the IO device reference
            print("Audio capture stopped.")

    def set_volume(self, volume):
        """Adjust microphone capture volume (0.0 - 1.0)."""
        self.volume = max(0.0, min(1.0, volume))  # Clamp volume to valid range
        self.audio_source.setVolume(self.volume)  # Apply volume to the audio source
        print(f"Microphone volume set to {self.volume}")

# Example usage
mic_mixer = MicMixer()
if audio_matches_qt_format("mysound.mp3", mic_mixer.audio_format):
    print("Formats match!")
else:
    print("Formats do not match.")
