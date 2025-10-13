# Shared audio package constants
# Keep simple constants here to avoid circular imports between modules

DEFAULT_CHANNELS = 2  # 2 for stereo, 1 for mono
DEFAULT_SAMPLE_RATE = 48000  # 48kHz sample rate, standard for many services
AUDIO_OUTPUT_BUFFER_SIZE = 2048  # Buffer size for audio output
AUDIO_PROCESS_INTERVAL_SEC = 0.011  # 11ms processing interval
AUDIO_PROCESS_INTERVAL_MS = 11  # 11ms interval for processing audio
MIC_GAIN = 1.0 # Default
MUSIC_GAIN = 0.2
INT16_MAX = 32767
INT16_SCALE = 32768.0

# Expose a clean public API for package imports
__all__ = [
	'DEFAULT_CHANNELS',
	'DEFAULT_SAMPLE_RATE',
	'AUDIO_OUTPUT_BUFFER_SIZE',
	'AUDIO_PROCESS_INTERVAL_SEC',
	'AUDIO_PROCESS_INTERVAL_MS',
	'MIC_GAIN',
	'MUSIC_GAIN',
	'INT16_MAX',
	'INT16_SCALE',
]
