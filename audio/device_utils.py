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
    # Prefer searching audio outputs (devices you can write to). If nothing
    # is found there, try audio inputs as a fallback (some systems expose the
    # virtual cable in a way that is more appropriate to the capture side).
    for devices_getter in (QMediaDevices.audioOutputs, QMediaDevices.audioInputs):
        try:
            devices = devices_getter()
        except Exception:
            devices = []

        for device in devices:
            description = device.description().lower()
            if "vb-audio" in description or "vb-cable" in description or "cable" in description:
                print(f"Found VB-Cable device: {device.description()}")
                return device

    return None