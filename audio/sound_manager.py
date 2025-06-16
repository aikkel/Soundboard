from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from pydub import AudioSegment
from audio.mic_mixer import MicMixer

class SoundManager:
    def __init__(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.mic_mixer = MicMixer()

    def play_sound(self, file_path):
        """Plays a sound file and loads it into the microphone mixer."""
        if not file_path:
            print("Error: No file path provided.")
            return

        print(f"Playing sound: {file_path}")

        # Load the sound file and convert to raw data
        try:
            audio = AudioSegment.from_file(file_path)
            sound_data = audio.raw_data
        except Exception as e:
            print(f"Failed to load sound file: {e}")
            return

        # Load sound data into the mic mixer
        self.mic_mixer.load_sound(sound_data)

        # Play the sound through the normal audio output
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()
        print("Sound is playing through the audio output.")