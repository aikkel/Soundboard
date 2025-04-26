import subprocess

def install_vbcable(installer_path):
    try:
        result = subprocess.run(
            [installer_path],
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("VB-Cable installation launched successfully. User interaction required.")
    except subprocess.CalledProcessError as e:
        print(f"VB-Cable installation failed: {e.stderr.decode()}")

# Path to the VB-Cable installer
installer_path = "VBCABLE_Driver_Pack45/VBCABLE_Setup_x64.exe"
install_vbcable(installer_path)
