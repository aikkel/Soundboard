from PyQt6.QtMultimedia import QAudioSource, QAudioSink, QMediaDevices, QAudioFormat
from PyQt6.QtCore import QIODevice, QTimer, QByteArray
import numpy as np

class MicMixer:
    def __init__(self, audio_device=None, output_device=None):
        self.audio_device = audio_device or QMediaDevices.defaultAudioInput()
        self.output_device = output_device or self.get_vbcable_output_device()
        if not self.audio_device or not self.output_device:
            raise RuntimeError("Audio input or output device not found.")

        self.audio_format = self.audio_device.preferredFormat()
        self.audio_source = QAudioSource(self.audio_device, self.audio_format)
        self.audio_sink = QAudioSink(self.output_device, self.audio_format)

        self.mic_buffer = bytearray()
        self.sound_buffer = bytearray()

        self.io_device = self.audio_source.start()
        if not isinstance(self.io_device, QIODevice):
            raise RuntimeError("Failed to start audio input. Ensure a valid QIODevice is provided.")
        self.io_device.readyRead.connect(self.capture_audio)

        self.output_io = self.audio_sink.start()

        self.volume = 0.65
        self.audio_source.setVolume(self.volume)
        self.audio_sink.setVolume(0.9)

        # Timer to mix and output audio every 20ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.mix_and_output)
        print("Timer started.")
        self.timer.start(20)

    def get_vbcable_output_device(self):
        print("get_vbcable_output_device called.")  # Debugging
        for device in QMediaDevices.audioOutputs():
            print(f"Found output device: {device.description()}")  # Debugging
            if "VB-Audio Virtual Cable" in device.description():
                print("Selected VB-Cable output device.")  # Debugging
                return device
        print("VB-Cable output device not found.")  # Debugging
        return None
    
    def capture_audio(self):
        from PyQt6.QtMultimedia import QAudio
        if self.io_device and self.audio_source.state() == QAudio.State.ActiveState:
            data = self.io_device.readAll()
            print(f"Captured {len(data)} bytes from microphone.")  # Debugging
            if data:
                self.mic_buffer.extend(data.data())
            else:
                print("No data captured from microphone.")  # Debugging

    def load_soundboard_audio(self, pcm_bytes):
        """Append PCM bytes to the soundboard buffer (call this when playing a sound)."""
        print(f"Loading soundboard audio of size {len(pcm_bytes)} bytes.")  # Debugging
        self.sound_buffer.extend(pcm_bytes)

    def mix_and_output(self):
        chunk_size = 2048
        if len(self.mic_buffer) < chunk_size or len(self.sound_buffer) < chunk_size:
            # Suppress repeated messages when buffers are empty
            if not hasattr(self, "_last_mix_warning") or not self._last_mix_warning:
                print(f"Not enough data to mix. Mic buffer: {len(self.mic_buffer)}, Sound buffer: {len(self.sound_buffer)}")  # Debugging
                self._last_mix_warning = True
            return

        # Reset the warning flag when mixing resumes
        self._last_mix_warning = False
        print("Mixing audio...")  # Debugging

        mic_chunk = self.mic_buffer[:chunk_size]
        sound_chunk = self.sound_buffer[:chunk_size]
        self.mic_buffer = self.mic_buffer[chunk_size:]
        self.sound_buffer = self.sound_buffer[chunk_size:]

        # Mix (assuming 16-bit PCM, mono or stereo)
        mic_np = np.frombuffer(mic_chunk, dtype=np.int16)
        sound_np = np.frombuffer(sound_chunk, dtype=np.int16)
        mixed = mic_np.astype(np.int32) + sound_np.astype(np.int32)
        mixed = np.clip(mixed, -32768, 32767).astype(np.int16)

        self.output_io.write(QByteArray(mixed.tobytes()))

    def stop(self):
        self.audio_source.stop()
        self.audio_sink.stop()
        self.timer.stop()

    def set_volume(self, volume):
            """Adjust microphone capture volume (0.0 - 1.0)."""
            self.volume = max(0.0, min(1.0, volume))  # Clamp volume to valid range
            self.audio_source.setVolume(self.volume)  # Apply volume to the audio source
            print(f"Microphone volume set to {self.volume}")