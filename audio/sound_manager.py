# from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
# from PyQt6.QtCore import QUrl
# from pydub import AudioSegment
# from audio.mic_mixer import MicMixer

from audio.mic_mixer import MicMixer
from pydub import AudioSegment


class SoundManager:
	def __init__(self, route_to_vbcable_only=False):
		# Create mic mixer and optionally route playback to VB-Cable only
		self.mic_mixer = MicMixer(route_to_vbcable_only=route_to_vbcable_only)

	def play_sound(self, file_path):
		"""Plays a sound file via the mic mixer so it gets mixed into the
		microphone stream without changing the mic device."""
		if not file_path:
			print("Error: No file path provided.")
			return

		print(f"Playing sound through mixer: {file_path}")
		try:
			audio = AudioSegment.from_file(file_path)
			sound_data = audio.raw_data
		except Exception as e:
			print(f"Failed to load sound file: {e}")
			return

		self.mic_mixer.load_sound(sound_data)