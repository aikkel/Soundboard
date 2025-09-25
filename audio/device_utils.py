from PyQt6.QtMultimedia import QMediaDevices

def list_audio_devices():
    print("\n=== Available Audio Input Devices ===")
    for i, device in enumerate(QMediaDevices.audioInputs()):
        print(f"{i}: {device.description()}")

    print("\n=== Available Audio Output Devices ===")
    for i, device in enumerate(QMediaDevices.audioOutputs()):
        print(f"{i}: {device.description()}")

def get_vbcable_output_device():
    """Find VB-Cable output device."""
    devices = QMediaDevices.audioOutputs()
    for device in devices:
        description = device.description().lower()
        if "vb-audio" in description or "cable" in description:
            print(f"Found VB-Cable device: {device.description()}")
            return device
    return None