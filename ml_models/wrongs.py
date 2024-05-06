import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget

"""
GUI utility to look through images that classifier incorrectly classified

Run with python3 wrongs.py, then use right arrow to look through images.
"""

GAME_CLASS = "game"
COMMERCIAL_CLASS = "com"


class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.finished = False
        self.setMinimumSize(800, 500)
        self.setWindowTitle("Pictures the model wrongly classified")
        self.image_label = QLabel(parent=self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.images = MainWindow.loadPics()

        self.instruction_label = QLabel()
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.instruction_label.setStyleSheet(
            "QLabel {font-size: 30px; margin-top: 20px}"
        )

        self.layout2 = QGridLayout()
        self.layout2.addWidget(self.image_label, 0, 0)
        self.layout2.addWidget(self.instruction_label, 1, 0)

        self.setLayout(self.layout2)

        self.changePic()

    @staticmethod
    def loadPics():
        with open("wrongs.txt") as f:
            lines = [
                l.removesuffix("\n")
                for l in f.readlines()
                if l.startswith(("FN: ", "FP: "))
            ]
        return [{"type": l[:2], "path": l[4:]} for l in lines]

    def changePic(self):
        try:
            self.current_pic = self.images.pop()
            print(self.current_pic)
            self.pix_map = QPixmap(self.current_pic["path"]).scaledToWidth(600)
            self.image_label.setPixmap(self.pix_map)
            self.instruction_label.setText(self.current_pic["type"])
        except IndexError:
            self.instruction_label.setText("All images viewed.")
            self.finished = True

    def keyPressEvent(self, a0):
        if not self.finished:
            if Qt.Key(a0.key()).name == "Key_Right":
                self.changePic()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
