import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import tempfile

def is_ffmpeg_installed():
    """Check if ffmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None

def download_and_extract_ffmpeg(dest_dir):
    """Download and extract FFmpeg static build for Windows."""
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(tempfile.gettempdir(), "ffmpeg.zip")

    print("Downloading FFmpeg...")
    try:
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        print("Download complete.")
    except Exception as e:
        print("Failed to download FFmpeg:", e)
        sys.exit(1)

    print("Extracting FFmpeg...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        print("Extraction complete.")
    except zipfile.BadZipFile:
        print("Downloaded zip file is corrupted.")
        sys.exit(1)

    # Search for ffmpeg.exe inside extracted folder
    for root, dirs, files in os.walk(dest_dir):
        print(f"Searching in: {root}")
        if any(f.lower() == "ffmpeg.exe" for f in files):
            return root

    raise FileNotFoundError("ffmpeg.exe not found after extraction.")

def add_to_path(dir_path):
    """Add the given directory to the user PATH environment variable."""
    current_path = os.environ.get("PATH", "")
    new_path = f"{current_path};{dir_path}"

    # Check for duplication
    if dir_path in current_path:
        print("FFmpeg path already in PATH.")
    else:
        if len(new_path) > 1024:
            print("Warning: New PATH may exceed the 1024 character limit for setx.")
        try:
            subprocess.run(f'setx PATH "{new_path}"', shell=True, check=True)
            print(f"Added {dir_path} to user PATH.")
        except subprocess.CalledProcessError as e:
            print("Failed to update PATH using setx:", e)

    # Update current session's PATH
    os.environ["PATH"] += os.pathsep + dir_path
    print("Updated PATH for current session (will not persist after reboot).")
    print("You may need to restart your terminal or computer to apply changes system-wide.")

def main():
    if is_ffmpeg_installed():
        print("FFmpeg is already installed and available in PATH.")
        return

    print("FFmpeg not found. Installing...")
    home_dir = os.path.expanduser("~")
    ffmpeg_dir = os.path.join(home_dir, "ffmpeg")
    os.makedirs(ffmpeg_dir, exist_ok=True)

    try:
        bin_dir = download_and_extract_ffmpeg(ffmpeg_dir)
        add_to_path(bin_dir)
        print("FFmpeg installation complete.")
    except Exception as e:
        print("An error occurred during installation:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
# This script checks if FFmpeg is installed, and if not, downloads and installs it.
# It adds the FFmpeg binary directory to the user's PATH environment variable.