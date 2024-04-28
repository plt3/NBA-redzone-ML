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


class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

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
            self.current_pic = os.path.join("screenshots", self.screenshots.pop())
            self.pix_map = QPixmap(self.current_pic).scaledToWidth(600)
            self.image_label.setPixmap(self.pix_map)
        except IndexError:
            self.instruction_label.setText("All images labeled.")
            self.finished = True

    def keyPressEvent(self, a0):
        if not self.finished:
            if Qt.Key(a0.key()).name == "Key_Right":
                new_name = self.current_pic.replace(
                    f".{FILE_EXTENSION}", f"_{GAME_CLASS}.{FILE_EXTENSION}"
                )
                os.rename(self.current_pic, new_name)
                self.changePic()
            elif Qt.Key(a0.key()).name == "Key_Left":
                new_name = self.current_pic.replace(
                    f".{FILE_EXTENSION}", f"_{COMMERCIAL_CLASS}.{FILE_EXTENSION}"
                )
                os.rename(self.current_pic, new_name)
                self.changePic()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
