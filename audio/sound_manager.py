from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

class SoundManager:
    def __init__(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

    def play_sound(self, file_path):
        """Plays a sound file."""
        if not file_path:
            print("Error: No file path provided.")
            return

        print(f"Playing sound from: {file_path}")  # Debugging
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()

    def stop_sound(self):
        """Stops the currently playing sound."""
        self.media_player.stop()

    def set_volume(self, volume):
        """Sets the playback volume (0 to 100)."""
        self.audio_output.setVolume(volume / 100.0)

    def is_playing(self):
        """Checks if a sound is currently playing."""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
