from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QGridLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
import ui.grids

def create_play_panel(main_window):
    scene = QWidget()
    layout = QVBoxLayout()
    
    main_window.search_bar = QLineEdit()
    main_window.search_bar.setPlaceholderText("Search")
    layout.addWidget(main_window.search_bar)
    
    # Add a grid layout for the file grid
    main_window.grid_layout = QGridLayout()
    layout.addLayout(main_window.grid_layout)
    
    # Placeholder label for the grid
    placeholder_label = QLabel("No files loaded. Connect a folder to populate.")
    placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_window.grid_layout.addWidget(placeholder_label, 0, 0, 1, 4)  # Spanning 4 columns
    
    # Add a Refresh button
    main_window.refresh_button = QPushButton("Refresh")
    main_window.refresh_button.clicked.connect(lambda: ui.grids.refresh_grid(main_window))
    layout.addWidget(main_window.refresh_button)
    
    main_window.settings_button = QPushButton("Settings")
    main_window.settings_button.clicked.connect(lambda: main_window.central_widget.setCurrentWidget(main_window.scene1))
    layout.addWidget(main_window.settings_button)
    
    scene.setLayout(layout)
    return scene