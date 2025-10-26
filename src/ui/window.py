import os
from pathlib import Path
from typing import Dict, Tuple

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QSizePolicy
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


ROOT = Path(__file__).parent.resolve()


class StyleUpdateSignal(QObject):
    style_updated = Signal(str)


class StyleHandler(FileSystemEventHandler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def on_modified(self, event):
        if event.src_path.endswith(".css"):
            self.signal.style_updated.emit(event.src_path)


class BaseWindow(QWidget):
    def __init__(self, rel_style_path: str, expand: bool = False):
        super().__init__()
        if expand:
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
        self.styles_path = ROOT / rel_style_path
        self.styles: Dict = dict()
        self.signal = StyleUpdateSignal()
        self.signal.style_updated.connect(self.reload_style)

        self.observer = Observer()
        self.start_watchdog()
        for filename in os.listdir(self.styles_path):
            self.reload_style(str(self.styles_path / filename), update=False)
        self.setStyleSheet(self.current_stylesheet)

    def start_watchdog(self):
        handler = StyleHandler(self.signal)
        self.observer.schedule(handler, path=str(self.styles_path), recursive=False)
        self.observer.start()

    @property
    def current_stylesheet(self):
        return "\n".join(style for style in self.styles.values())

    def reload_style(self, filepath: str, update: bool = True):
        try:
            rel_path = filepath.replace(str(ROOT), '').strip("\\")
            with open(filepath, "r", encoding="utf-8") as f:
                self.styles[rel_path] = f.read()
            if update:
                self.setStyleSheet(self.current_stylesheet)
            return True
        except Exception as err:
            print(f"Error reloading stylesheet: {err}")
            return False

    def closeEvent(self, event):
        self.observer.stop()
        try:
            self.observer.join(timeout=1.0)
        except RuntimeError:
            print("Observer stopped")
        event.accept()
