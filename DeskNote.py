import sys
import os
import time
import subprocess
import ctypes
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

def get_script_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# Constants
OUTPUT_DIR = os.path.join(get_script_directory(), "temp")
WALLPAPER_FONT = "Arial"
WALLPAPER_POINTSIZE = "72"
WALLPAPER_BG = "black"
WALLPAPER_FILL = "white"
WALLPAPER_SIZE = "1920x1080"
LOG_FOLDER_NAME = "daily_note"
LOG_FILE_NAME = "note_log.txt"

def get_log_file_path():
    script_dir = get_script_directory()
    notes_folder = os.path.join(script_dir, LOG_FOLDER_NAME)
    if not os.path.exists(notes_folder):
        os.makedirs(notes_folder)
    return os.path.join(notes_folder, LOG_FILE_NAME)

def retrieve_log():
    notes_file = get_log_file_path()
    if not os.path.exists(notes_file):
        return "No notes logged yet."
    with open(notes_file, "r", encoding="utf-8") as f:
        return f.read()

def log_text(note_text):
    notes_file = get_log_file_path()
    if not os.path.exists(notes_file):
        with open(notes_file, "w", encoding="utf-8"):
            pass
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\nDeskNote {timestamp_str}:\n{note_text}\n=====================\n"
    with open(notes_file, "r", encoding="utf-8") as f:
        old_contents = f.read()
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write(log_entry + old_contents)

def process_commands(text):
    flags = {"log": True, "exit": False, "continue": False, "error": False}
    text = text.replace("/time", time.strftime("%H:%M:%S"))
    text = text.replace("/date", time.strftime("%d/%m/%Y"))
    text = text.replace("/now", time.strftime("%d/%m/%Y %H:%M:%S"))
    if "/nolog" in text.lower():
        flags["log"] = False
        text = text.replace("/nolog", "")
    if "/exit" in text.lower():
        flags["exit"] = True
        text = text.replace("/exit", "")
    if "/continue" in text.lower():
        flags["continue"] = True
        text = text.replace("/continue", "")
    allowed_commands = ["time", "date", "now", "nolog", "exit", "continue", "strip", "textbf", "textit", "underline"]
    commands = re.findall(r'/([a-zA-Z]+)(?:\{[^}]+\})?', text)
    for cmd in commands:
        if cmd.lower() not in allowed_commands:
            flags["error"] = True
            QMessageBox.critical(None, "Invalid Command", f"Inappropriate command '/{cmd}' used.")
            break
    return text, flags

def apply_continue_modification(text):
    existing_entry = retrieve_log()
    parts = existing_entry.split("\n")
    if len(parts) > 2:
        existing_entry = "\n".join(parts[2:])
        existing_entry = existing_entry.split("\n=====================\n")[0].rstrip()
    else:
        existing_entry = ""
    strip_commands = re.findall(r'/strip\{([^}]+)\}', text)
    if strip_commands:
        lines = existing_entry.splitlines()
        for token in strip_commands:
            lines = [line for line in lines if token not in line]
        existing_entry = "\n".join(lines)
        text = re.sub(r'/strip\{[^}]+\}', '', text)
    return f"{existing_entry}{text}"

def apply_formatting(text):
    text = re.sub(r'/textbf\{([^}]+)\}', r'<b>\1</b>', text)
    text = re.sub(r'/textit\{([^}]+)\}', r'<i>\1</i>', text)
    text = re.sub(r'/underline\{([^}]+)\}', r'<u>\1</u>', text)
    return text

def create_wallpaper(text):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    timestamp = int(time.time())
    output_image = os.path.join(OUTPUT_DIR, f"wallpaper_{timestamp}.jpg")
    safe_text = text.replace('"', '\\"')
    command = [
        "magick",
        "-background", WALLPAPER_BG,
        "-fill", WALLPAPER_FILL,
        "-pointsize", WALLPAPER_POINTSIZE,
        "-size", "1800x",
        f'pango:{safe_text}',
        "-size", WALLPAPER_SIZE,
        "xc:black",
        "+swap",
        "-gravity", "northwest",
        "-geometry", "+50+50",
        "-composite",
        output_image
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Error", f"Error generating image:\n{e}")
        return None
    return output_image

def set_wallpaper(image_path):
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 1
    SPIF_SENDWININICHANGE = 2
    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, image_path, SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
    )
    return result

class DeskNoteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("DeskNote")
        # Set the logo (ensure "logo.png" is in the same directory)
        self.setWindowIcon(QIcon(os.path.join(get_script_directory(), "logo.png")))
        self.setFixedSize(1000, 800)
        # Apply dark theme for the main window
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        instructions = (
            "<div style='text-align:left; font-size:24px; color:#ffffff;'>"
            "<b>Enter text for your wallpaper:</b><br><br>"
            "- Use <i>/date</i>, <i>/time</i>, or <i>/now</i> to insert current date/time.<br>"
            "- Use <i>/nolog</i> to <u>NOT</u> log your note.<br>"
            "- Use <i>/exit</i> to close after submission.<br>"
            "- Use <i>/continue</i> to append to previous note (with optional <i>/strip{token}</i> to remove lines).<br>"
            "- Use <i>/textbf{}</i>, <i>/textit{}</i>, <i>/underline{}</i> for formatting.<br>"
            "</div>"
        )
        self.instructions_label = QLabel(instructions)
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.instructions_label)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                padding: 8px;
                font-size: 24px;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.text_edit)
        
        self.submit_button = QPushButton("Set Wallpaper")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: #ffffff;
                border: 1px solid #555;
                padding: 10px;
                font-size: 24px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6d6d6d;
            }
        """)
        self.submit_button.clicked.connect(self.submit_text)
        layout.addWidget(self.submit_button)
    
    def submit_text(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Input Required", "Please enter some text for the wallpaper.")
            return
        
        processed_text, flags = process_commands(text)
        if flags.get("error"):
            return
        
        if "/strip" in processed_text and not flags["continue"]:
            QMessageBox.warning(self, "Invalid Command", "Use '/continue' to strip lines from previous note.")
            return
        
        if flags["continue"]:
            processed_text = apply_continue_modification(processed_text)
        
        processed_text = apply_formatting(processed_text)
        safe_text = processed_text.replace('"', '\\"')
        image_path = create_wallpaper(safe_text)
        if image_path is None:
            return
        
        if set_wallpaper(image_path):
            QMessageBox.information(self, "Success", "Wallpaper set successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to set wallpaper.")
        
        if flags["log"]:
            log_text(safe_text)
        
        if flags["exit"]:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeskNoteApp()
    window.show()
    sys.exit(app.exec_())
