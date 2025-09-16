import os
from PyQt6.QtWidgets import QFileDialog
from utils.config import save_settings
from ui.grids import populate_sound_buttons

def apply_settings(self):
    """Apply settings to the UI components."""
    print("Applying settings...")  # Debugging
    self.dial_mc.setValue(int(self.settings.get("mic_volume", 1.00) * 100))
    self.dial_sb.setValue(int(self.settings.get("speaker_volume", 1.00) * 100))
    last_selected_mic = self.settings.get("last_selected_mic")
    if last_selected_mic:
        index = self.input_device.findText(last_selected_mic)
        if index != -1:
            self.input_device.setCurrentIndex(index)

    # Load the last selected folder and populate the grid
    last_folder = self.settings.get("last_sound_folder")
    if last_folder and os.path.exists(last_folder):
        print(f"Loading sounds from last folder: {last_folder}")  # Debugging
        populate_sound_buttons(self, last_folder)
    else:
        print("No valid folder found in settings.")  # Debugging


def load_sounds(self):
    """Open a folder dialog to select a sound folder and populate the grid."""
    folder = QFileDialog.getExistingDirectory(self, "Select Sound Folder")
    if folder:
        self.settings["last_sound_folder"] = folder  # Save the selected folder to settings
        save_settings(self.settings)  # Persist the updated settings
        print(f"Selected folder saved: {folder}")  # Debugging
        populate_sound_buttons(self, folder)


###
# def start_mic_capture(self):
#         """Start capturing audio from the microphone."""
#         if not self.mic_mixer:
#             selected_device = self.input_device.currentData()  # Get the selected QAudioDevice
#             self.mic_mixer = MicMixer(audio_device=selected_device)  # Pass the selected device
#             print(f"Microphone capture started with device: {selected_device.description()}")
#         else:
#             print("Microphone is already capturing.")

#     def stop_mic_capture(self):
#         """Stop capturing audio from the microphone."""
#         if self.mic_mixer:
#             self.mic_mixer.stop_capture()  # Stop the mic mixer
#             self.mic_mixer = None  # Reset the mic mixer
#             print("Microphone capture stopped.")
#         else:
#             print("Microphone is not capturing.")