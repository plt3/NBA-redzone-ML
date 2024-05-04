import os
import sys

from PIL import Image, ImageDraw


class ImageCropper:
    """Class to crop screenshots of window containing stream to just be left with
    stream and none of the rest of the window. For use in preprocessing screenshots
    for image classifier

    NOTE: assumes that window is in minimal Brave theme (no address bar) and that
    page around stream is one color (use Fullscreen Anything extension to fullscreen
    stream within window)
    """

    NUM_STEPS = 50

    def __init__(self, image_path):
        self.image_path = image_path
        self.img = Image.open(self.image_path)
        self.width, self.height = self.img.size
        self.pixel_map = self.img.load()

    def find_top_bottom_edge(self, edge_type) -> int:
        if edge_type == "top":
            # this starts at right of browser window header
            start_pixel = (self.width - 50, 20)
            increment = 1
        elif edge_type == "bottom":
            start_pixel = (self.width - 50, self.height - 20)
            increment = -1
        else:
            return 0

        lines = []
        for column in range(
            start_pixel[0],
            self.width // 2,
            -1 * (start_pixel[0] - self.width // 2) // self.NUM_STEPS,
        ):
            last_ten_pixels = []
            edge_start = 0
            for row in range(start_pixel[1], self.height // 2, increment):
                if len(last_ten_pixels) < 10:
                    last_ten_pixels.append(self.pixel_map[column, row])
                else:
                    del last_ten_pixels[0]
                    last_ten_pixels.append(self.pixel_map[column, row])
                if len(set(last_ten_pixels)) >= 5:
                    edge_offset = 0
                    for index, pixel in enumerate(last_ten_pixels):
                        if pixel != last_ten_pixels[0]:
                            edge_offset = index
                            break
                    edge_start = row - increment * (10 - edge_offset)
                    lines.append(edge_start)
                    break

        if len(lines) == 0:
            raise Exception(f"{edge_type} edge not found.")
        return max(set(lines), key=lines.count)

    def find_left_right_edge(self, edge_type, top_bottom=None) -> int:
        if edge_type == "left":
            # this starts below the left of browser window header
            start_pixel = (0, 100)
            increment = 1
        elif edge_type == "right":
            start_pixel = (self.width - 1, 100)
            increment = -1
        else:
            return 0

        if top_bottom is None:
            top = start_pixel[1]
            bottom = self.height // 2
        else:
            top, bottom = top_bottom

        lines = []
        for row in range(
            top,
            bottom,
            (bottom - top) // self.NUM_STEPS,
        ):
            last_ten_pixels = []
            edge_start = 0
            for column in range(start_pixel[0], self.width // 2, increment):
                if len(last_ten_pixels) < 10:
                    last_ten_pixels.append(self.pixel_map[column, row])
                else:
                    del last_ten_pixels[0]
                    last_ten_pixels.append(self.pixel_map[column, row])
                if len(set(last_ten_pixels)) >= 5:
                    edge_offset = 0
                    for index, pixel in enumerate(last_ten_pixels):
                        if pixel != last_ten_pixels[0]:
                            edge_offset = index
                            break
                    edge_start = column - increment * (
                        len(last_ten_pixels) - edge_offset
                    )
                    lines.append(edge_start)
                    break

        if len(lines) == 0:
            raise Exception(f"{edge_type} edge not found.")
        return max(set(lines), key=lines.count)

    def get_crop_points(self, crop_left_right):
        top = self.find_top_bottom_edge("top")
        bottom = self.find_top_bottom_edge("bottom")
        # often just need to crop top/bottom
        if crop_left_right:
            left = self.find_left_right_edge("left", (top, bottom))
            right = self.find_left_right_edge("right", (top, bottom))
        else:
            left = 0
            right = self.width - 1

        return top, bottom, left, right

    def view_crop(self, crop_left_right=True):
        top, bottom, left, right = self.get_crop_points(crop_left_right)

        draw = ImageDraw.Draw(self.img)
        draw.line((left, top, right, top), fill="red", width=1)
        draw.line((left, bottom, right, bottom), fill="red", width=1)
        draw.line((left, top, left, bottom), fill="red", width=1)
        draw.line((right, top, right, bottom), fill="red", width=1)
        self.img.show()

    def crop_image(self, crop_left_right=True, output_path=None):
        top, bottom, left, right = self.get_crop_points(crop_left_right)

        if bottom - top < self.height // 4 or right - left < self.width // 4:
            print(
                f"WARNING: cropping {self.image_path} resulted in an unusually small"
                " image. Consider checking file manually."
            )

        if output_path is None:
            filename, ext = os.path.splitext(self.image_path)
            output_path = f"{filename}_cropped{ext}"

        self.img.crop((left, top, right, bottom)).save(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"USAGE: python3 {sys.argv[0]} /path/to/image.jpg")
    else:
        cropper = ImageCropper(sys.argv[1])
        cropper.crop_image()
