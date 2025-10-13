# This is a soundboard which pipes thrpugh microphone to a virtual mic that can be be picked up on discord. 
**At present moment it only plays 48Khz soundclips.** 

## Soundboard Setup

### Requirements
- Python 3.10+ (https://www.python.org/downloads/)
- ffmpeg (https://ffmpeg.org/download.html) — add to your PATH
- VB-Cable (https://vb-audio.com/Cable/) — install and reboot

### Installation
1. Clone this repo
2. Open a terminal in the project folder
3. Run: pip install -r requirements.txt

### Running
python -m ui.main_window

### Troubleshooting
- If you see "ffmpeg not found", install ffmpeg and add it to your PATH.
- remember to set discord or other target output to use VB-Cable output as microphone

Third-Party Dependencies
========================

This project uses the following third-party tools:

**1. VB-Cable**
---------
VB-Cable is a virtual audio device for Windows that allows audio routing between applications.
- Website: https://vb-audio.com/Cable/
- Usage: Used for virtual audio input/output in the soundboard.
========================

**2. FFmpeg**
---------
FFmpeg is a complete, cross-platform solution to record, convert and stream audio and video.
- Website: https://ffmpeg.org/
- Usage: Used for audio format conversion and processing.

Please ensure both VB-Cable and FFmpeg are installed and available in your system PATH for full functionality.
========================