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
        
        print(f"Input device preferred format: {self.format.sampleRate()}Hz, {self.format.channelCount()} channels, {self.format.sampleFormat()}")
        
        # Check if output device supports this format, if not use its preferred format
        if not self.output_device.isFormatSupported(self.format):
            print("Output device doesn't support input format, using output preferred format")
            self.format = self.output_device.preferredFormat()
        
        print(f"Final format: {self.format.sampleRate()}Hz, {self.format.channelCount()} channels, {self.format.sampleFormat()}")

    def init_audio_streams(self):
        try:
            # Create audio source and sink with the format
            self.audio_input = QAudioSource(self.audio_device, self.format)
            self.audio_output = QAudioSink(self.output_device, self.format)
            
            # Set buffer sizes
            self.audio_input.setBufferSize(4096)
            self.audio_output.setBufferSize(4096)
            
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
            
            # Set up timer for audio processing
            self.timer = QTimer()
            self.timer.timeout.connect(self.mix_audio)
            self.timer.start(20)  # Process every 20ms
            
        except Exception as e:
            print(f"Error initializing audio streams: {e}")
            self.cleanup()
            raise

    def load_sound(self, sound_data):
        """Load sound data for mixing - convert to match current audio format"""
        try:
            if isinstance(sound_data, np.ndarray):
                # If it's already a numpy array, ensure it's the right type
                if sound_data.dtype == np.int16:
                    # Convert int16 to float32 (normalize to -1.0 to 1.0 range)
                    sound_float = sound_data.astype(np.float32) / 32768.0
                else:
                    sound_float = sound_data.astype(np.float32)
            else:
                # Convert bytes to numpy array (assuming int16) then to float32
                sound_int16 = np.frombuffer(sound_data, dtype=np.int16)
                sound_float = sound_int16.astype(np.float32) / 32768.0
            
            # Handle channel conversion
            target_channels = self.format.channelCount()
            
            if len(sound_float.shape) == 1:  # Mono input
                if target_channels == 2:  # Convert mono to stereo
                    sound_float = np.column_stack((sound_float, sound_float))
                    print(f"Converted mono sound to stereo")
                elif target_channels == 1:  # Keep as mono
                    pass
                else:
                    print(f"Warning: Unsupported channel count: {target_channels}")
                    return
            else:  # Stereo or multi-channel input
                if target_channels == 1:  # Convert to mono
                    sound_float = np.mean(sound_float, axis=1)
                    print(f"Converted stereo sound to mono")
                elif target_channels == 2:  # Keep as stereo
                    pass
                else:
                    print(f"Warning: Unsupported channel count: {target_channels}")
                    return
            
            self.sound_buffer = sound_float
            self.sound_position = 0
            print(f"Loaded sound buffer with {len(self.sound_buffer)} samples, {target_channels} channels")
            
        except Exception as e:
            print(f"Error loading sound: {e}")
            self.sound_buffer = np.array([], dtype=np.float32)

    def mix_audio(self):
        if not self.is_active or self.input_stream is None or self.output_stream is None:
            return
            
        try:
            # Read available microphone data
            available_bytes = self.input_stream.bytesAvailable()
            if available_bytes <= 0:
                return
                
            # Limit read size to prevent buffer overflow
            read_size = min(available_bytes, 4096)
            mic_data = self.input_stream.read(read_size)
            
            if not mic_data or len(mic_data) == 0:
                return

            # Convert to numpy array based on sample format
            if self.format.sampleFormat() == QAudioFormat.SampleFormat.Float:
                mic_array = np.frombuffer(mic_data, dtype=np.float32)
            elif self.format.sampleFormat() == QAudioFormat.SampleFormat.Int16:
                mic_int16 = np.frombuffer(mic_data, dtype=np.int16)
                mic_array = mic_int16.astype(np.float32) / 32768.0
            else:
                print(f"Unsupported sample format: {self.format.sampleFormat()}")
                return
            
            if len(mic_array) == 0:
                return
            
            # Handle channel count for mixing
            channels = self.format.channelCount()
            if channels > 1:
                # Reshape for multi-channel audio
                mic_array = mic_array.reshape(-1, channels)
                frames = len(mic_array)
            else:
                frames = len(mic_array)
            
            # Initialize mixed array with mic data
            mixed_array = mic_array.copy()
            
            # Mix in sound buffer if available
            if len(self.sound_buffer) > 0 and self.sound_position < len(self.sound_buffer):
                if channels > 1 and len(self.sound_buffer.shape) > 1:
                    # Multi-channel mixing
                    frames_needed = frames
                    frames_available = len(self.sound_buffer) - self.sound_position
                    frames_to_use = min(frames_needed, frames_available)
                    
                    if frames_to_use > 0:
                        sound_chunk = self.sound_buffer[self.sound_position:self.sound_position + frames_to_use]
                        
                        # Mix the audio (simple addition with volume control)
                        mixed_section = mixed_array[:frames_to_use] + (sound_chunk * 0.5)  # Reduce sound volume
                        
                        # Clip to prevent distortion
                        mixed_section = np.clip(mixed_section, -1.0, 1.0)
                        mixed_array[:frames_to_use] = mixed_section
                        
                        self.sound_position += frames_to_use
                else:
                    # Mono mixing
                    samples_needed = len(mic_array) if channels == 1 else len(mic_array)
                    samples_available = len(self.sound_buffer) - self.sound_position
                    samples_to_use = min(samples_needed, samples_available)
                    
                    if samples_to_use > 0:
                        sound_chunk = self.sound_buffer[self.sound_position:self.sound_position + samples_to_use]
                        
                        if channels == 1:
                            mixed_section = mic_array[:samples_to_use] + (sound_chunk * 0.5)
                        else:
                            # Broadcast mono sound to stereo
                            sound_stereo = np.column_stack((sound_chunk, sound_chunk))[:samples_to_use//2]
                            mixed_section = mixed_array[:len(sound_stereo)] + (sound_stereo * 0.5)
                        
                        mixed_section = np.clip(mixed_section, -1.0, 1.0)
                        if channels == 1:
                            mixed_array[:samples_to_use] = mixed_section
                        else:
                            mixed_array[:len(mixed_section)] = mixed_section
                        
                        self.sound_position += samples_to_use
                
                # Reset sound position if we've reached the end
                if self.sound_position >= len(self.sound_buffer):
                    # self.sound_position = 0  # Uncomment to loop the sound
                    self.sound_buffer = np.array([], dtype=np.float32)  # Stop after playing once
                    print("Sound finished playing")
            
            # Convert back to bytes for output
            if self.format.sampleFormat() == QAudioFormat.SampleFormat.Float:
                mixed_data = mixed_array.tobytes()
            elif self.format.sampleFormat() == QAudioFormat.SampleFormat.Int16:
                mixed_int16 = (mixed_array * 32767).astype(np.int16)
                mixed_data = mixed_int16.tobytes()
            else:
                return
            
            # Write mixed audio to output
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