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
        self.sound_buffer = np.array([], dtype=np.int16)
        self.sound_position = 0
        self.is_active = False
        
        # Set up audio format
        self.setup_audio_format()
        self.init_audio_streams()

    def setup_audio_format(self):
        """Set up a consistent audio format for both input and output"""
        self.format = QAudioFormat()
        self.format.setSampleRate(48000)
        self.format.setChannelCount(1)  # Mono
        self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        
        # Check if the format is supported by both devices
        if not self.audio_device.isFormatSupported(self.format):
            print("Warning: Audio format not supported by input device, using preferred format")
            self.format = self.audio_device.preferredFormat()
        
        if not self.output_device.isFormatSupported(self.format):
            print("Warning: Audio format not supported by output device")

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
        """Load sound data for mixing"""
        if isinstance(sound_data, np.ndarray):
            self.sound_buffer = sound_data.astype(np.int16)
        else:
            # Convert bytes to numpy array
            self.sound_buffer = np.frombuffer(sound_data, dtype=np.int16)
        
        self.sound_position = 0
        print(f"Loaded sound buffer with {len(self.sound_buffer)} samples")

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

            # Convert to numpy array
            mic_array = np.frombuffer(mic_data, dtype=np.int16)
            
            if len(mic_array) == 0:
                return
            
            # Initialize mixed array with mic data
            mixed_array = mic_array.copy()
            
            # Mix in sound buffer if available
            if len(self.sound_buffer) > 0 and self.sound_position < len(self.sound_buffer):
                # Calculate how much of the sound buffer to use
                samples_needed = len(mic_array)
                samples_available = len(self.sound_buffer) - self.sound_position
                samples_to_use = min(samples_needed, samples_available)
                
                if samples_to_use > 0:
                    # Get the sound data to mix
                    sound_chunk = self.sound_buffer[self.sound_position:self.sound_position + samples_to_use]
                    
                    # Mix the audio (add and clip to prevent overflow)
                    mixed_section = np.add(mic_array[:samples_to_use].astype(np.int32), 
                                         sound_chunk.astype(np.int32))
                    
                    # Clip to int16 range
                    mixed_section = np.clip(mixed_section, -32768, 32767).astype(np.int16)
                    mixed_array[:samples_to_use] = mixed_section
                    
                    # Update sound position
                    self.sound_position += samples_to_use
                    
                    # Reset sound position if we've reached the end
                    if self.sound_position >= len(self.sound_buffer):
                        self.sound_position = 0  # Loop the sound
            
            # Write mixed audio to output
            mixed_data = mixed_array.tobytes()
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