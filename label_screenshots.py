import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget

from take_screenshots import FILE_EXTENSION

"""
GUI utility to easily label screenshots as being either NBA games or commercials.

Run with python3 label_screenshots.py, then use left/right arrows to add correct
label to end of image's filename. Stop by quitting the Python app.
"""

GAME_CLASS = "game"
COMMERCIAL_CLASS = "com"
SORTED_DATA_DIRECTORY = "sorted_screenshots"


class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        os.makedirs(os.path.join(SORTED_DATA_DIRECTORY, GAME_CLASS), exist_ok=True)
        os.makedirs(
            os.path.join(SORTED_DATA_DIRECTORY, COMMERCIAL_CLASS), exist_ok=True
        )

        self.finished = False
        self.setMinimumSize(800, 500)
        self.setWindowTitle("Label screenshots")
        self.image_label = QLabel(parent=self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.instruction_label = QLabel(
            "Left arrow: commercial        Right arrow: game"
        )
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.instruction_label.setStyleSheet(
            "QLabel {font-size: 30px; margin-top: 20px}"
        )

        self.layout2 = QGridLayout()
        self.layout2.addWidget(self.image_label, 0, 0)
        self.layout2.addWidget(self.instruction_label, 1, 0)

        self.setLayout(self.layout2)

        # only get files that haven't already been labeled
        self.screenshots = [
            pic
            for pic in os.listdir("screenshots")
            if GAME_CLASS not in pic
            and COMMERCIAL_CLASS not in pic
            and pic.endswith(FILE_EXTENSION)
        ]
        self.screenshots.sort(reverse=True)

        self.changePic()

    def changePic(self):
        try:
            self.current_pic = self.screenshots.pop()
            self.current_path = os.path.join("screenshots", self.current_pic)
            self.pix_map = QPixmap(self.current_path).scaledToWidth(600)
            self.image_label.setPixmap(self.pix_map)
        except IndexError:
            self.instruction_label.setText("All images labeled.")
            self.finished = True

    def keyPressEvent(self, a0):
        if not self.finished:
            if Qt.Key(a0.key()).name == "Key_Right":
                img_class = GAME_CLASS
            elif Qt.Key(a0.key()).name == "Key_Left":
                img_class = COMMERCIAL_CLASS
            else:
                return

            new_fname = self.current_pic.replace(
                f".{FILE_EXTENSION}", f"_{img_class}.{FILE_EXTENSION}"
            )
            new_path = os.path.join(SORTED_DATA_DIRECTORY, img_class, new_fname)

            if not os.path.exists(new_path):
                os.rename(self.current_path, new_path)
            else:
                raise Exception(f"{new_path} already exists???")
            self.changePic()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
