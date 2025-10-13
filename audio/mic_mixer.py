from PyQt6.QtMultimedia import QAudioSource, QAudioSink, QMediaDevices, QAudioFormat
from PyQt6.QtCore import QTimer
import numpy as np
from audio.audio_format_utils import decode_to_pcm, duplicate_mono_to_stereo, ensure_channel_count
from audio.device_utils import list_audio_devices, get_vbcable_output_device
from . import DEFAULT_CHANNELS, DEFAULT_SAMPLE_RATE, AUDIO_OUTPUT_BUFFER_SIZE, AUDIO_PROCESS_INTERVAL_SEC, AUDIO_PROCESS_INTERVAL_MS, MIC_GAIN, MUSIC_GAIN, INT16_MAX, INT16_SCALE

class MicMixer:
    def __init__(self, audio_device=None, output_devices=None, route_to_vbcable_only=False):
        """Create a MicMixer.

        route_to_vbcable_only: when True, prefer routing playback only to the
        VB-Cable device (if present) and also keep the microphone input device
        unchanged. This helps prevent changing the system default mic/device
        when playing sounds.
        """
        self.route_to_vbcable_only = route_to_vbcable_only

        # Do NOT change the system microphone/device. Use provided audio_device
        # or the system default audio input for capture only.
        self.audio_device = self._select_audio_device(audio_device)
        self.output_devices = self._setup_output_devices(output_devices)
        self._print_output_devices()

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
            print("Microphone initialized successfully.")
        except Exception as e:
            print(f"Microphone initialization failed: {e}")
            raise

    def _select_audio_device(self, audio_device):
        # If caller passed a device that is actually the VB-Cable virtual
        # output (or an output-only device), we must NOT use it as the input
        # capture device. Instead fall back to the system default audio input
        # so the real microphone remains active. The VB-Cable device will be
        # used for output routing instead.
        vb_cable = get_vbcable_output_device()

        # If audio_device looks like the VB-Cable device, ignore it for input
        if audio_device is not None:
            try:
                desc = audio_device.description().lower()
            except Exception:
                desc = ""

            if vb_cable is not None and (audio_device == vb_cable or "vb-audio" in desc or "vb-cable" in desc or "cable" in desc):
                fallback = QMediaDevices.defaultAudioInput()
                print(f"Provided device '{audio_device.description()}' appears to be a virtual cable/output device. Using system default input '{fallback.description()}' for capture instead.")
                device = fallback
            else:
                device = audio_device
        else:
            device = QMediaDevices.defaultAudioInput()

        if not device:
            print("No microphone device found during registration.")
            raise RuntimeError("No microphone device found.")

        print(f"Registered microphone: {device.description()}")
        return device

    def _setup_output_devices(self, output_devices):
        if output_devices is not None:
            return output_devices
        vb_cable = get_vbcable_output_device()
        default_output = QMediaDevices.defaultAudioOutput()

        # If route_to_vbcable_only is True, prefer returning only the virtual
        # cable device so playback goes to the cable and doesn't affect the
        # default output device used by the system/Discord.
        if self.route_to_vbcable_only and vb_cable:
            return [vb_cable]

        devices = [vb_cable] if vb_cable else []
        if default_output and (not vb_cable or default_output != vb_cable):
            devices.append(default_output)
        return devices

    def _print_output_devices(self):
        print("Using audio output devices:")
        for dev in self.output_devices:
            print(f"   - {dev.description()}")

    def setup_audio_format(self):
        """Set up audio format based on what devices actually support"""
        # Start with the input device's preferred format
        # Use the microphone's preferred format for capture but force the
        # output format to a compatible common format for playback so we don't
        # try to reconfigure the input device when opening sinks.
        mic_pref = self.audio_device.preferredFormat()
        self.format = mic_pref
        # Force output to Int16 for compatibility with VB-Cable/Discord.
        # Keep sample rate and channels at app defaults to avoid resampling
        # the capture device; sinks will accept the format we provide.
        self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.format.setChannelCount(DEFAULT_CHANNELS)
        self.format.setSampleRate(DEFAULT_SAMPLE_RATE)

        print(f"Forced output format: {self.format.sampleRate()}Hz, {self.format.channelCount()} channels, {self.format.sampleFormat()}")

    def init_audio_streams(self):
        try:
            # Create audio source and sink with the format
            self.audio_input = QAudioSource(self.audio_device, self.format)
            self.input_stream = self.audio_input.start()
            self.audio_output_objs = []
            self.output_streams = []
            # If requested, ensure VB-Cable is included in outputs before starting
            if self.route_to_vbcable_only:
                vb = get_vbcable_output_device()
                if vb and vb not in self.output_devices:
                    self.output_devices.insert(0, vb)
            for dev in self.output_devices:
                ao = QAudioSink(dev, self.format)
                ao.setBufferSize(AUDIO_OUTPUT_BUFFER_SIZE)
                stream = ao.start()
                self.audio_output_objs.append(ao)
                self.output_streams.append(stream)
                print(f"Started output stream for device: {dev.description()}")

            if self.input_stream is None:
                print("Input stream does not contain microphone data.")
                raise RuntimeError(f"Failed to initialize input stream for device: {self.audio_device.description()}")
            else:
                print("Input stream contains microphone data.")

            print(f"Audio streams initialized successfully")
            print(f"Input format: {self.format.sampleRate()}Hz, {self.format.channelCount()} channels, {self.format.sampleFormat()}")

            self.is_active = True

            # Set up timer for audio processing (11ms for lower latency)
            self.timer = QTimer()
            self.timer.timeout.connect(self.mix_audio)
            self.timer.start(AUDIO_PROCESS_INTERVAL_MS)  # Process every 11ms

        except Exception as e:
            print(f"Error initializing audio streams: {e}")
            self.cleanup()
            raise

    def pcm_to_float32(self, pcm_array):
        """Convert PCM numpy array to float32 in range [-1.0, 1.0]."""
        if pcm_array.dtype == np.int16:
            return pcm_array.astype(np.float32) / INT16_SCALE
        else:
            return pcm_array.astype(np.float32)

    def prepare_sound_buffer(self, sound_data):
        """Decode and prepare sound data as a float32 numpy array for mixing."""
        sample_rate = self.format.sampleRate()
        channels = self.format.channelCount()
        bytes_per_sample = self.format.bytesPerSample()

        # Only decode if not already a numpy array
        if isinstance(sound_data, np.ndarray):
            pcm_array = sound_data
        else:
            pcm_array = decode_to_pcm(sound_data, sample_rate, channels, bytes_per_sample)

        if pcm_array is None or len(pcm_array) == 0:
            return np.array([], dtype=np.float32)

        # Convert to float32 for mixing
        sound_float = self.pcm_to_float32(pcm_array)

        # Duplicate mono channel to stereo if needed
        sound_float = duplicate_mono_to_stereo(sound_float, channels)

        # Ensure buffer is always (frames, channels)
        sound_float = ensure_channel_count(sound_float, channels)

        return sound_float

    def load_sound(self, sound_data):
        """Load sound data for mixing - convert to match current audio format"""
        try:
            sound_float = self.prepare_sound_buffer(sound_data)
            if sound_float is None or len(sound_float) == 0:
                print("Failed to decode or convert sound file")
                self.sound_buffer = np.array([], dtype=np.float32)
                return

            self.sound_buffer = sound_float
            self.sound_position = 0
            print(f"Loaded sound buffer with {self.sound_buffer.shape} (frames, channels)")
        except Exception as e:
            print(f"Error loading sound: {e}")
            self.sound_buffer = np.array([], dtype=np.float32)

    def ensure_mic_array_shape(self, mic_array, expected_samples, frames_per_tick, channels):
        """Ensure mic_array is the correct size and shape for mixing."""
        if mic_array.size != expected_samples:
            mic_array = np.zeros(expected_samples, dtype=np.float32)
        return mic_array.reshape(frames_per_tick, channels)

    def mix_audio(self):
        if not self.is_active or self.input_stream is None or not self.output_streams:
            return

        try:
            frames_per_tick = int(self.format.sampleRate() * AUDIO_PROCESS_INTERVAL_SEC)  # 11ms of audio
            channels = self.format.channelCount()
            bytes_per_sample = self.format.bytesPerSample()
            bytes_per_frame = channels * bytes_per_sample
            total_bytes = frames_per_tick * bytes_per_frame

            mic_data = self.input_stream.read(total_bytes)
            input_format = self.audio_device.preferredFormat().sampleFormat()
            expected_samples = frames_per_tick * channels

            if mic_data and len(mic_data) == total_bytes:
                if input_format == QAudioFormat.SampleFormat.Int16:
                    mic_array = np.frombuffer(mic_data, dtype=np.int16).astype(np.float32) / INT16_SCALE
                elif input_format == QAudioFormat.SampleFormat.Float:
                    mic_array = np.frombuffer(mic_data, dtype=np.float32)
                else:
                    mic_array = np.zeros(expected_samples, dtype=np.float32)
            else:
                mic_array = np.zeros(expected_samples, dtype=np.float32)

            mic_array = self.ensure_mic_array_shape(mic_array, expected_samples, frames_per_tick, channels)

            # Prepare sound_chunk (music) for mixing
            if self.sound_buffer is not None and len(self.sound_buffer) > 0 and self.sound_position < len(self.sound_buffer):
                sound_chunk = self.sound_buffer[self.sound_position:self.sound_position + frames_per_tick]
                sound_chunk = self.pad_sound_chunk(sound_chunk, frames_per_tick, channels)
                self.sound_position += frames_per_tick
                if self.sound_position >= len(self.sound_buffer):
                    self.sound_buffer = np.array([], dtype=np.float32)
                    print("Sound finished playing")
            else:
                sound_chunk = np.zeros((frames_per_tick, channels), dtype=np.float32)

            mic_gain = MIC_GAIN   # Full volume for mic
            music_gain = MUSIC_GAIN # Lower volume for music

            mixed_array = (mic_array * mic_gain) + (sound_chunk * music_gain)
            mixed_array = np.clip(mixed_array, -1.0, 1.0)

            mixed_int16 = (mixed_array * INT16_MAX).astype(np.int16)
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

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

    def pad_sound_chunk(self, sound_chunk, target_frames, channels):
        """Pad sound_chunk with zeros to reach target_frames length."""
        if sound_chunk.shape[0] < target_frames:
            pad_shape = (target_frames - sound_chunk.shape[0], channels)
            sound_chunk = np.vstack([sound_chunk, np.zeros(pad_shape, dtype=np.float32)])
        return sound_chunk