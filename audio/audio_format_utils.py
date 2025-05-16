import os
from pydub import AudioSegment

def audio_matches_qt_format(audio_path, qt_format):
    """
    Check if an audio file (any format supported by pydub/ffmpeg) matches the given QAudioFormat.
    """
    audio = AudioSegment.from_file(audio_path)
    channels = audio.channels
    sample_width = audio.sample_width  # in bytes
    sample_rate = audio.frame_rate

    qt_channels = qt_format.channelCount()
    qt_sample_rate = qt_format.sampleRate()
    qt_bytes_per_sample = qt_format.bytesPerSample()

    return (
        channels == qt_channels and
        sample_width == qt_bytes_per_sample and
        sample_rate == qt_sample_rate
    )

# --- Test code below ---

# if __name__ == "__main__":
#     # Mock QAudioFormat for testing (replace with real one in your app)
#     class MockQtFormat:
#         def channelCount(self): return 2
#         def sampleRate(self): return 48000
#         def bytesPerSample(self): return 2

#     qt_format = MockQtFormat()
#     test_folder = r"e:/Code Projects/Soundboard/Testfolder"

#     for filename in os.listdir(test_folder):
#         file_path = os.path.join(test_folder, filename)
#         try:
#             result = audio_matches_qt_format(file_path, qt_format)
#             print(f"{filename}: Format match: {result}")
#         except Exception as e:
#             print(f"{filename}: Error - {e}")