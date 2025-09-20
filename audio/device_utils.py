from PyQt6.QtMultimedia import QMediaDevices

def list_audio_devices():
    print("\n=== Available Audio Input Devices ===")
    for i, device in enumerate(QMediaDevices.audioInputs()):
        print(f"{i}: {device.description()}")

    print("\n=== Available Audio Output Devices ===")
    for i, device in enumerate(QMediaDevices.audioOutputs()):
        print(f"{i}: {device.description()}")