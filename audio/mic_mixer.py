from PyQt6.QtMultimedia import QAudioSource, QAudioSink, QMediaDevices, QAudioFormat
from PyQt6.QtCore import QIODevice, QTimer, QByteArray
import numpy as np
from audio.audio_format_utils import decode_to_pcm  # Add this import at the top
#comments needed to reuploade
class MicMixer:
    def __init__(self, audio_device=None, output_devices=None):
        self.audio_device = audio_device or QMediaDevices.defaultAudioInput()
        if not self.audio_device:
            print("❌ No microphone device found during registration.")
            raise RuntimeError("No microphone device found.")
        else:
            print(f"✅ Registered microphone: {self.audio_device.description()}")

        # Support multiple output devices
        if output_devices is None:
            vb_cable = self.get_vbcable_output_device()
            default_output = QMediaDevices.defaultAudioOutput()
            self.output_devices = [vb_cable] if vb_cable else []
            if default_output and (not vb_cable or default_output != vb_cable):
                self.output_devices.append(default_output)
        else:
            self.output_devices = output_devices

        print("✅ Using audio output devices:")
        for dev in self.output_devices:
            print(f"   - {dev.description()}")

        self.input_stream = None
        self.output_streams = []
        self.sound_buffer = np.array([], dtype=np.float32)
        self.sound_position = 0
        self.is_active = False

        # Set up audio format
        self.setup_audio_format()

        # Init mic check
        try:
            self.init_audio_streams()
            print("✅ Microphone initialized successfully.")
        except Exception as e:
            print(f"❌ Microphone initialization failed: {e}")
            raise

    def setup_audio_format(self):
        """Set up audio format based on what devices actually support"""
        # Start with the input device's preferred format
        self.format = self.audio_device.preferredFormat()

        # Force output to Int16 for compatibility with VB-Cable/Discord
        self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.format.setChannelCount(2)  # Stereo is safest for Discord
        self.format.setSampleRate(48000)  # 48000Hz is standard for Discord

        print(f"Forced output format: {self.format.sampleRate()}Hz, {self.format.channelCount()} channels, {self.format.sampleFormat()}")

    def init_audio_streams(self):
        try:
            # Create audio source and sink with the format
            self.audio_input = QAudioSource(self.audio_device, self.format)
            self.input_stream = self.audio_input.start()
            self.audio_output_objs = []
            self.output_streams = []
            for dev in self.output_devices:
                ao = QAudioSink(dev, self.format)
                ao.setBufferSize(2048)
                stream = ao.start()
                self.audio_output_objs.append(ao)
                self.output_streams.append(stream)
                print(f"Started output stream for device: {dev.description()}")

            if self.input_stream is None:
                print("❌ Input stream does not contain microphone data.")
                raise RuntimeError(f"Failed to initialize input stream for device: {self.audio_device.description()}")
            else:
                print("✅ Input stream contains microphone data.")

            print(f"Audio streams initialized successfully")
            print(f"Input format: {self.format.sampleRate()}Hz, {self.format.channelCount()} channels, {self.format.sampleFormat()}")
            
            self.is_active = True
            
            # Set up timer for audio processing (11ms for lower latency)
            self.timer = QTimer()
            self.timer.timeout.connect(self.mix_audio)
            self.timer.start(11)  # Process every 11ms

        except Exception as e:
            print(f"Error initializing audio streams: {e}")
            self.cleanup()
            raise

    def load_sound(self, sound_data):
        """Load sound data for mixing - convert to match current audio format"""
        try:
            sample_rate = self.format.sampleRate()
            channels = self.format.channelCount()
            bytes_per_sample = self.format.bytesPerSample()

            # Only decode if not already a numpy array
            if isinstance(sound_data, np.ndarray):
                pcm_array = sound_data
            else:
                pcm_array = decode_to_pcm(sound_data, sample_rate, channels, bytes_per_sample)

            if pcm_array is None or len(pcm_array) == 0:
                print("Failed to decode or convert sound file")
                self.sound_buffer = np.array([], dtype=np.float32)
                return

            # Convert to float32 for mixing
            if pcm_array.dtype == np.int16:
                sound_float = pcm_array.astype(np.float32) / 32768.0
            else:
                sound_float = pcm_array.astype(np.float32)

            # If mono but output is stereo, duplicate channel
            if sound_float.ndim == 1 and channels == 2:
                sound_float = np.column_stack([sound_float, sound_float])
            elif sound_float.ndim == 2 and sound_float.shape[1] == 1 and channels == 2:
                sound_float = np.column_stack([sound_float[:, 0], sound_float[:, 0]])

            # Ensure buffer is always (frames, channels)
            if sound_float.ndim == 1:
                sound_float = sound_float.reshape(-1, channels)
            elif sound_float.ndim == 2 and sound_float.shape[1] != channels:
                sound_float = sound_float[:, :channels]

            self.sound_buffer = sound_float
            self.sound_position = 0
            print(f"Loaded sound buffer with {self.sound_buffer.shape} (frames, channels)")
        except Exception as e:
            print(f"Error loading sound: {e}")
            self.sound_buffer = np.array([], dtype=np.float32)

    def mix_audio(self):
        if not self.is_active or self.input_stream is None or not self.output_streams:
            return

        try:
            frames_per_tick = int(self.format.sampleRate() * 0.011)  # 11ms of audio
            channels = self.format.channelCount()
            bytes_per_sample = self.format.bytesPerSample()
            bytes_per_frame = channels * bytes_per_sample
            total_bytes = frames_per_tick * bytes_per_frame

            mic_data = self.input_stream.read(total_bytes)
            input_format = self.audio_device.preferredFormat().sampleFormat()
            expected_samples = frames_per_tick * channels

            if mic_data and len(mic_data) == total_bytes:
                if input_format == QAudioFormat.SampleFormat.Int16:
                    mic_array = np.frombuffer(mic_data, dtype=np.int16).astype(np.float32) / 32768.0
                elif input_format == QAudioFormat.SampleFormat.Float:
                    mic_array = np.frombuffer(mic_data, dtype=np.float32)
                else:
                    mic_array = np.zeros(expected_samples, dtype=np.float32)
            else:
                mic_array = np.zeros(expected_samples, dtype=np.float32)

            # Ensure correct shape
            if mic_array.size != expected_samples:
                mic_array = np.zeros(expected_samples, dtype=np.float32)
            mic_array = mic_array.reshape(frames_per_tick, channels)

            # Prepare sound_chunk (music) for mixing
            if self.sound_buffer is not None and len(self.sound_buffer) > 0 and self.sound_position < len(self.sound_buffer):
                sound_chunk = self.sound_buffer[self.sound_position:self.sound_position + frames_per_tick]
                if sound_chunk.shape[0] < frames_per_tick:
                    pad_shape = (frames_per_tick - sound_chunk.shape[0], channels)
                    sound_chunk = np.vstack([sound_chunk, np.zeros(pad_shape, dtype=np.float32)])
                self.sound_position += frames_per_tick
                if self.sound_position >= len(self.sound_buffer):
                    self.sound_buffer = np.array([], dtype=np.float32)
                    print("Sound finished playing")
            else:
                sound_chunk = np.zeros((frames_per_tick, channels), dtype=np.float32)

            mic_gain = 1.0   # Full volume for mic
            music_gain = 0.2 # Lower volume for music

            mixed_array = (mic_array * mic_gain) + (sound_chunk * music_gain)
            mixed_array = np.clip(mixed_array, -1.0, 1.0)

            mixed_int16 = (mixed_array * 32767).astype(np.int16)
            mixed_data = mixed_int16.flatten(order='C').tobytes()

            for stream in self.output_streams:
                bytes_written = stream.write(mixed_data)
                if bytes_written < 0:
                    print("Error writing to output stream")
        except Exception as e:
            print(f"Error in mix_audio: {e}")

    def stop_capture(self):
        """Stop audio capture and mixing"""
        self.is_active = False
        
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        self.cleanup()
        print("Audio capture stopped")

    def cleanup(self):
        """Clean up audio resources"""
        try:
            if hasattr(self, 'audio_input') and self.audio_input:
                self.audio_input.stop()
            if hasattr(self, 'audio_output_objs'):
                for ao in self.audio_output_objs:
                    ao.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        self.input_stream = None
        self.output_streams = []
        self.audio_input = None
        self.audio_output_objs = []

    def get_vbcable_output_device(self):
        """Find VB-Cable output device"""
        devices = QMediaDevices.audioOutputs()
        for device in devices:
            description = device.description().lower()
            if "vb-audio" in description or "cable" in description:
                print(f"Found VB-Cable device: {device.description()}")
                return device
        return None

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Debug function to list available devices
def list_audio_devices():
    print("\n=== Available Audio Input Devices ===")
    for i, device in enumerate(QMediaDevices.audioInputs()):
        print(f"{i}: {device.description()}")
        
    print("\n=== Available Audio Output Devices ===")
    for i, device in enumerate(QMediaDevices.audioOutputs()):
        print(f"{i}: {device.description()}")

if __name__ == "__main__":
    # For testing
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    list_audio_devices()