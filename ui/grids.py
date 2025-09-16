import os
from PyQt6.QtWidgets import QPushButton

def populate_sound_buttons(self, folder):
        # Clear existing buttons in the grid
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Get a list of sound files in the folder
        sound_files = [f for f in os.listdir(folder) if f.endswith(('.mp3', '.wav', '.ogg'))]
        
        row, col = 0, 0
        for sound in sound_files:
            file_path = os.path.join(folder, sound)  # Full path to the sound file
            btn = QPushButton(sound)
            btn.clicked.connect(lambda checked, path=file_path: self.play_selected_sound(path))  # Connect button to playback
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
          
def refresh_grid(self):
    """Reload the sound grid using the last selected folder from settings."""
    folder = self.settings.get("last_sound_folder")
    if folder and os.path.exists(folder):
        populate_sound_buttons(self, folder)
        print(f"Grid refreshed from folder: {folder}")
    else:
        print("No valid folder found in settings.")