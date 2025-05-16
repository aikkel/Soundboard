import subprocess
import os

# Build the installer path relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
installer_path = os.path.join(BASE_DIR, "VBCABLE_Driver_Pack45", "VBCABLE_Setup_x64.exe")

def is_vbcable_installed():
    # Use PowerShell to check for the VB-Audio Virtual Cable device
    ps_command = (
        "Get-PnpDevice | Where-Object { $_.FriendlyName -like '*VB-Audio Virtual Cable*' }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
        )
        return "VB-Audio Virtual Cable" in result.stdout
    except Exception as e:
        print(f"Error checking VB-Cable installation: {e}")
        return False

def install_vbcable(installer_path):
    try:
        # Use a string command and wrap the path in quotes for shell=True
        command = f'"{installer_path}"'
        result = subprocess.run(
            command,
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("VB-Cable installation launched successfully. User interaction required.")
    except subprocess.CalledProcessError as e:
        print(f"VB-Cable installation failed: {e.stderr.decode()}")

if is_vbcable_installed():
    print("VB-Cable is already installed. Skipping installation.")
else:
    install_vbcable(installer_path)