from PyQt6.QtMultimedia import QAudioSource, QAudioSink, QMediaDevices, QAudioFormat
from PyQt6.QtCore import QIODevice, QTimer, QByteArray
import numpy as np
from audio.audio_format_utils import decode_to_pcm  # Add this import at the top
#comments needed to reuploade
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
        else:
            print(f"Using audio output device: {self.output_device.description()}")

        self.input_stream = None
        self.output_stream = None
        self.sound_buffer = np.array([], dtype=np.float32)
        self.sound_position = 0
        self.is_active = False
        
        # Set up audio format
        self.setup_audio_format()
        self.init_audio_streams()

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
            self.audio_output = QAudioSink(self.output_device, self.format)
            
            # Set buffer sizes (smaller for lower latency)
            self.audio_input.setBufferSize(2048) 
            self.audio_output.setBufferSize(2048)
            
            # Start the streams
            self.input_stream = self.audio_input.start()
            self.output_stream = self.audio_output.start()
            
            if self.input_stream is None:
                raise RuntimeError(f"Failed to initialize input stream for device: {self.audio_device.description()}")
            
            if self.output_stream is None:
                raise RuntimeError(f"Failed to initialize output stream for device: {self.output_device.description()}")
                
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
        if not self.is_active or self.input_stream is None or self.output_stream is None:
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
            mixed_array = mic_array.copy()

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

            # Mix with volume balance (adjust as needed)
            mic_volume = 0.8
            music_volume = 0.7
            mixed_array = (mic_array * mic_volume) + (sound_chunk * music_volume)
            mixed_array = np.clip(mixed_array, -1.0, 1.0)

            mixed_int16 = (mixed_array * 32767).astype(np.int16)
            mixed_data = mixed_int16.flatten(order='C').tobytes()

            bytes_written = self.output_stream.write(mixed_data)
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
            if self.audio_input:
                self.audio_input.stop()
            if self.audio_output:
                self.audio_output.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        self.input_stream = None
        self.output_stream = None
        self.audio_input = None
        self.audio_output = None

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