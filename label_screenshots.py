import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget

from take_screenshots import FILE_EXTENSION

"""
GUI utility to easily label screenshots as being either NBA games or commercials.

Run with python3 label_screenshots.py, then use left/right arrows to add correct
label to end of image's filename. Up arrow goes back one image to fix errors made
when labeling. D key deletes an image.

Stop by quitting the Python app.
"""

GAME_CLASS = "game"
COMMERCIAL_CLASS = "com"
UNSORTED_DATA_DIRECTORY = "screenshots"
SORTED_DATA_DIRECTORY = "sorted_screenshots"


class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        os.makedirs(os.path.join(SORTED_DATA_DIRECTORY, GAME_CLASS), exist_ok=True)
        os.makedirs(
            os.path.join(SORTED_DATA_DIRECTORY, COMMERCIAL_CLASS), exist_ok=True
        )

        self.finished = False
        self.setMinimumSize(800, 550)
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
        self.number_label = QLabel()
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.number_label.setStyleSheet("QLabel {font-size: 25px; margin-top: 10px}")

        self.layout2 = QGridLayout()
        self.layout2.addWidget(self.image_label, 0, 0)
        self.layout2.addWidget(self.instruction_label, 1, 0)
        self.layout2.addWidget(self.number_label, 2, 0)

        self.setLayout(self.layout2)

        # only get files that haven't already been labeled
        self.screenshots = [
            pic
            for pic in os.listdir(UNSORTED_DATA_DIRECTORY)
            if GAME_CLASS not in pic
            and COMMERCIAL_CLASS not in pic
            and pic.endswith(FILE_EXTENSION)
        ]
        self.screenshots.sort()

        self.screenshot_index = 0
        self.screenshot_actions = {}

        self.changePic(0)

    def changePic(self, increment=1):
        try:
            self.screenshot_index += increment
            self.current_pic = self.screenshots[self.screenshot_index]
            self.current_path = os.path.join(UNSORTED_DATA_DIRECTORY, self.current_pic)
            self.pix_map = QPixmap(self.current_path).scaledToWidth(600)
            self.image_label.setPixmap(self.pix_map)
            self.number_label.setText(
                f"{self.screenshot_index}/{len(self.screenshots)} images labeled"
            )
        except IndexError:
            self.instruction_label.setText("All images labeled.")
            self.number_label.setText("")
            self.finished = True

    def keyPressEvent(self, a0):
        if not self.finished and a0 is not None:
            if Qt.Key(a0.key()).name in ["Key_Right", "Key_Left"]:
                if Qt.Key(a0.key()).name == "Key_Right":
                    img_class = GAME_CLASS
                else:
                    img_class = COMMERCIAL_CLASS
                # rename file but don't move it yet, in case need to go back, etc.
                new_fname = self.current_pic.replace(
                    f".{FILE_EXTENSION}", f"_{img_class}.{FILE_EXTENSION}"
                )
                new_path = os.path.join(UNSORTED_DATA_DIRECTORY, new_fname)
                if not os.path.exists(new_path):
                    os.rename(self.current_path, new_path)
                else:
                    raise Exception(f"{new_path} already exists???")

                # add file to screenshot_actions to move after program ends
                if new_fname in self.screenshot_actions:
                    raise Exception(f"Already labeled a file as {new_path}???")

                self.screenshot_actions[new_fname] = img_class
                self.screenshots[self.screenshot_index] = new_fname
                self.changePic()
            elif Qt.Key(a0.key()).name == "Key_D":
                os.remove(self.current_path)
                del self.screenshots[self.screenshot_index]
                print(f"Removed {self.current_path}")
                self.changePic(0)
            elif Qt.Key(a0.key()).name == "Key_Up":
                if self.screenshot_index > 0:
                    # undo labeling of last image and go back one to allow corrections
                    prev_pic = self.screenshots[self.screenshot_index - 1]
                    old_fname = prev_pic.replace(
                        f"_{self.screenshot_actions[prev_pic]}.{FILE_EXTENSION}",
                        f".{FILE_EXTENSION}",
                    )
                    self.screenshots[self.screenshot_index - 1] = old_fname
                    del self.screenshot_actions[prev_pic]
                    new_path = os.path.join(UNSORTED_DATA_DIRECTORY, prev_pic)
                    old_path = os.path.join(UNSORTED_DATA_DIRECTORY, old_fname)
                    if not os.path.exists(old_path):
                        os.rename(new_path, old_path)
                        print(f"Renamed {new_path} to {old_path} to go back")
                    self.changePic(-1)

    def moveFiles(self):
        """Move labeled files to SORTED_DATA_DIRECTORY. To be called once after all the manual
        labeling has been done.
        """
        for filename, img_class in self.screenshot_actions.items():
            new_path = os.path.join(SORTED_DATA_DIRECTORY, img_class, filename)

            if not os.path.exists(new_path):
                os.rename(os.path.join(UNSORTED_DATA_DIRECTORY, filename), new_path)
            else:
                raise Exception(f"{new_path} already exists???")

        print(f"Labeled and moved {len(self.screenshot_actions)} images.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
    window.moveFiles()
