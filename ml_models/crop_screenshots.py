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

    def __init__(self, image_path: str) -> None:
        self.image_path = image_path
        self.img = Image.open(self.image_path)
        self.width, self.height = self.img.size
        self.pixel_map = self.img.load()

    def find_top_bottom_edge(self, edge_type: str) -> int:
        if edge_type == "top":
            # this starts at right of browser window header
            start_pixel = (self.width - 50, 20)
            increment = 1
        elif edge_type == "bottom":
            start_pixel = (self.width - 50, self.height - 20)
            increment = -1
        else:
            return 0

        if self.pixel_map is None:
            raise Exception("self.pixel_map is None")

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
            raise Exception(f"{edge_type} edge of {self.image_path} not found.")
        return max(set(lines), key=lines.count)

    def find_left_right_edge(
        self, edge_type: str, top_bottom: tuple[int, int] | None = None
    ) -> int:
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

        if self.pixel_map is None:
            raise Exception("self.pixel_map is None")

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
            raise Exception(f"{edge_type} edge of {self.image_path} not found.")
        return max(set(lines), key=lines.count)

    def find_training_image_edge(self, edge_type: str) -> int:
        """Use (relatively) simpler heuristic to crop training images: remove all
        rows of known pixel values (such as Brave Browser address bar or window
        background from Fullscreen Anything browser extension)"""
        # TODO: color below image could also be white: see sorted_screenshots/com/24-05-09_20-59-37_7605_com.jpg
        if edge_type == "top":
            # this starts at right of browser window header
            start_pixel = (self.width - 50, 20)
            increment = 1
        elif edge_type == "bottom":
            start_pixel = (self.width - 50, self.height - 20)
            increment = -1
        else:
            return 0

        if self.pixel_map is None:
            raise Exception("self.pixel_map is None")

        address_bar_colors = [
            (40, 40, 40),  # address bar when not focused
            (49, 49, 49),  # address bar when focused
            (36, 36, 36),  # sometimes the address bar is this color???
        ]
        other_window_colors = [
            (31, 31, 31),  # space below stream from Fullscreen Anything extension
            (34, 34, 34),  # space below stream from something else
            (0, 0, 0),  # just black, sometimes black bars above and below stream
        ]
        address_bar_lines = []
        lines = []
        for column in range(
            start_pixel[0],
            (3 * self.width) // 4,
            -1 * (start_pixel[0] - ((3 * self.width) // 4)) // self.NUM_STEPS,
        ):
            address_bar_found = False
            for row in range(start_pixel[1], self.height // 2, increment):
                if not address_bar_found and edge_type == "top":
                    if self.pixel_map[column, row] not in address_bar_colors:
                        address_bar_lines.append(row)
                        address_bar_found = True
                if (
                    self.pixel_map[column, row]
                    not in address_bar_colors + other_window_colors
                ):
                    lines.append(row)
                    break

        if len(lines) > 0:
            return max(set(lines), key=lines.count)
        else:
            if edge_type == "bottom":
                return self.height - 1
            if len(address_bar_lines) > 0:
                # fall back to just removing address bar if no new color found
                return max(set(address_bar_lines), key=address_bar_lines.count)
            else:
                raise Exception(f"{edge_type} edge of {self.image_path} not found.")

    def get_crop_points(
        self, training: bool, crop_left_right: bool
    ) -> tuple[int, int, int, int]:
        if training:
            top = self.find_training_image_edge("top")
            bottom = self.find_training_image_edge("bottom")
        else:
            top = self.find_top_bottom_edge("top")
            bottom = self.find_top_bottom_edge("bottom")
        # often just need to crop top/bottom
        if crop_left_right and not training:
            left = self.find_left_right_edge("left", (top, bottom))
            right = self.find_left_right_edge("right", (top, bottom))
        else:
            left = 0
            right = self.width - 1

        return top, bottom, left, right

    def view_crop(self, training: bool = False, crop_left_right: bool = True) -> None:
        top, bottom, left, right = self.get_crop_points(training, crop_left_right)

        draw_color = "green"
        draw_width = 5
        draw = ImageDraw.Draw(self.img)
        draw.line((left, top, right, top), fill=draw_color, width=draw_width)
        draw.line((left, bottom, right, bottom), fill=draw_color, width=draw_width)
        draw.line((left, top, left, bottom), fill=draw_color, width=draw_width)
        draw.line((right, top, right, bottom), fill=draw_color, width=draw_width)
        self.img.show()

    def crop_image(
        self,
        training: bool = False,
        crop_left_right: bool = True,
        resize_dims: tuple[int, int] | None = None,
    ) -> Image.Image:
        """NOTE: resize_dims must be of the form (width, height). training=True
        uses simpler algorithm to crop images by matching border colors and removing
        them. May not work for input images with different background colors depending
        on website/fullscreening browser extension.
        """
        top, bottom, left, right = self.get_crop_points(training, crop_left_right)

        if bottom - top < self.height // 4 or right - left < self.width // 4:
            print(
                f"WARNING: cropping {self.image_path} resulted in an unusually small"
                " image. Consider checking file manually."
            )

        cropped_img = self.img.crop((left, top, right, bottom))

        if resize_dims is not None:
            cropped_img = cropped_img.resize(resize_dims)

        return cropped_img

    def save_cropped_image(
        self,
        training: bool = False,
        crop_left_right: bool = True,
        resize_dims: tuple[int, int] | None = None,
        output_path: str | None = None,
    ) -> str:
        """NOTE: resize_dims must be of the form (width, height). training=True
        uses simpler algorithm to crop images by matching border colors and removing
        them. May not work for input images with different background colors depending
        on website/fullscreening browser extension.
        """
        cropped_img = self.crop_image(training, crop_left_right, resize_dims)

        if output_path is None:
            filename, ext = os.path.splitext(self.image_path)
            output_path = f"{filename}_cropped{ext}"

        cropped_img.save(output_path)

        return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"USAGE: python3 {sys.argv[0]} /path/to/image.jpg")
    else:
        cropper = ImageCropper(sys.argv[1])
        cropper.view_crop(False)
