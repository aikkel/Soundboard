import os
from pydub import AudioSegment
import numpy as np
from PyQt6.QtMultimedia import QAudioFormat

def audio_matches_qt_format(audio_path, qt_format):
    """
    Check if an audio file (any format supported by pydub/ffmpeg) matches the given QAudioFormat.
    """
    try:
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
    except Exception as e:
        print(f"Error checking audio format for {audio_path}: {e}")
        return False

def decode_to_pcm(file_path, target_sample_rate=48000, target_channels=1, target_sample_width=2):
    """
    Decode audio file to PCM format compatible with Qt audio
    
    Args:
        file_path: Path to audio file
        target_sample_rate: Target sample rate (default 48000)
        target_channels: Target number of channels (default 1 for mono)
        target_sample_width: Target sample width in bytes (default 2 for 16-bit)
    
    Returns:
        numpy array of PCM data (int16)
    """
    try:
        # Load audio file using pydub
        audio = AudioSegment.from_file(file_path)
        
        # Convert to target format
        audio = audio.set_frame_rate(target_sample_rate)
        audio = audio.set_channels(target_channels)
        audio = audio.set_sample_width(target_sample_width)
        
        # Get raw PCM data as bytes
        pcm_data = audio.raw_data
        
        # Convert to numpy array (assuming 16-bit samples)
        if target_sample_width == 2:
            pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        elif target_sample_width == 4:
            pcm_array = np.frombuffer(pcm_data, dtype=np.int32)
        else:
            # Fallback to int16
            pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        
        print(f"Decoded {file_path}: {len(pcm_array)} samples, {target_sample_rate}Hz, {target_channels} channels")
        return pcm_array
        
    except Exception as e:
        print(f"Error decoding {file_path}: {e}")
        return np.array([], dtype=np.int16)

def convert_audio_to_qt_format(file_path, qt_format):
    """
    Convert audio file to match Qt audio format
    
    Args:
        file_path: Path to audio file
        qt_format: QAudioFormat object
    
    Returns:
        numpy array of PCM data matching the Qt format
    """
    try:
        sample_rate = qt_format.sampleRate()
        channels = qt_format.channelCount()
        bytes_per_sample = qt_format.bytesPerSample()
        
        return decode_to_pcm(file_path, sample_rate, channels, bytes_per_sample)
        
    except Exception as e:
        print(f"Error converting audio to Qt format: {e}")
        return np.array([], dtype=np.int16)

def create_standard_qt_format():
    """
    Create a standard QAudioFormat for consistent audio processing
    """
    audio_format = QAudioFormat()
    audio_format.setSampleRate(48000)
    audio_format.setChannelCount(1)  # Mono
    audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    return audio_format

def validate_audio_file(file_path):
    """
    Validate that an audio file can be loaded and processed
    Args:
        file_path: Path to audio file
    Returns:
        dict with file info or None if invalid
    """
    try:
        audio = AudioSegment.from_file(file_path)
        return {
            'duration': len(audio) / 1000.0,  # Duration in seconds
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'sample_width': audio.sample_width,
            'format': 'valid'
        }
    except Exception as e:
        print(f"Invalid audio file {file_path}: {e}")
        return None

def duplicate_mono_to_stereo(sound_array, channels, default_channels=2):
    """Duplicate mono channel to stereo if needed."""
    if sound_array.ndim == 1 and channels == default_channels:
        return np.column_stack([sound_array, sound_array])
    elif sound_array.ndim == 2 and sound_array.shape[1] == 1 and channels == default_channels:
        return np.column_stack([sound_array[:, 0], sound_array[:, 0]])
    return sound_array

def ensure_channel_count(sound_array, channels):
    """Ensure sound_array has the correct number of channels."""
    if sound_array.ndim == 1:
        return sound_array.reshape(-1, channels)
    elif sound_array.ndim == 2 and sound_array.shape[1] != channels:
        return sound_array[:, :channels]
    return sound_array

# Test function
def test_audio_processing(test_folder_path=None):
    """
    Test audio processing functions
    """
    if not test_folder_path:
        print("No test folder provided")
        return
    
    if not os.path.exists(test_folder_path):
        print(f"Test folder does not exist: {test_folder_path}")
        return
    
    qt_format = create_standard_qt_format()
    print(f"Testing with Qt format: {qt_format.sampleRate()}Hz, {qt_format.channelCount()} channels, {qt_format.sampleFormat()}")
    
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')
    
    for filename in os.listdir(test_folder_path):
        if filename.lower().endswith(audio_extensions):
            file_path = os.path.join(test_folder_path, filename)
            print(f"\n--- Testing {filename} ---")
            
            # Validate file
            info = validate_audio_file(file_path)
            if info:
                print(f"File info: {info}")
            else:
                print("File validation failed")
                continue
            
            # Test format matching
            matches = audio_matches_qt_format(file_path, qt_format)
            print(f"Format matches Qt: {matches}")
            
            # Test PCM conversion
            pcm_data = decode_to_pcm(file_path)
            if len(pcm_data) > 0:
                print(f"PCM conversion successful: {len(pcm_data)} samples")
            else:
                print("PCM conversion failed")

# if __name__ == "__main__":
#     # Test with a folder if provided
#     test_folder = r"e:/Code Projects/Soundboard/Testfolder"  # Update this path
#     if os.path.exists(test_folder):
#         test_audio_processing(test_folder)
#     else:
#         print("Test folder not found, skipping tests")