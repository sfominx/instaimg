"""
Convert text to images
"""
from PIL import ImageFont, Image, ImageDraw
from typus import ru_typus
from typus.chars import NNBSP, NBSP

IMG_MODE = 'RGB'


class TextToImages:  # pylint: disable=too-many-instance-attributes
    """Make several images from text"""

    def __init__(self, width: int, height: int, font: ImageFont, background_color, font_color, alignment: str):
        self.font = font
        self.base_font_width, self.base_font_height = self.font.getsize('W')
        self.width = width
        self.height = height
        self.background_color = background_color
        self.image = None
        self._text_y = 0
        self._canvas = None
        self._max_width = self.width - 2.5 * self.base_font_width
        self._new_image = False
        self.font_color = font_color
        self.alignment = alignment

    def _reset_line(self):
        """Start new image, place cursor in the beginning of the image"""
        self._text_y = self.base_font_height
        self.image = Image.new(IMG_MODE, (self.width, self.height), color=self.background_color)
        self._canvas = ImageDraw.Draw(self.image)
        self._canvas.font = self.font
        self._new_image = True

    def _shift_line(self):
        """Shift cursor to new line"""
        self._new_image = False
        self._text_y += self.base_font_height + 2

    def _draw_line(self, text):
        """Print text line"""
        if self.alignment == 'justify':
            words = text.split()
            text_size = self.font.getsize(''.join(words))[0]

            if len(words) > 1:
                white_space_width = (self._max_width - text_size) // (len(words) - 1)
            else:
                white_space_width = 0

            text_start = self.base_font_width
            for word in words:
                self._canvas.text((text_start, self._text_y), word, fill=self.font_color)
                text_start += self.font.getsize(word)[0] + white_space_width

        elif self.alignment == 'right':
            text_width = self.font.getsize(text)[0]
            self._canvas.text((self.width - self.base_font_width - text_width, self._text_y),
                              text,
                              fill=self.font_color)

        elif self.alignment == 'center':
            text_width = self.font.getsize(text)[0]
            self._canvas.text(((self.width - text_width) // 2, self._text_y), text, fill=self.font_color)

        else:
            self._canvas.text((self.base_font_width, self._text_y), text, fill=self.font_color)

        if text.strip() or not self._new_image:
            self._shift_line()

    def split_text(self, text: str, typo: bool = True):
        """Split the text so that it fits into the images"""
        if typo:
            text_to_process = ru_typus(text).splitlines()
        else:
            text_to_process = text.splitlines()

        parts = []
        lines = []

        text_y = self.base_font_height

        for i_line in text_to_process:
            if self.font.getsize(i_line)[0] <= self._max_width:
                lines.append(i_line.replace(NNBSP, NBSP))
                text_y += self.base_font_height + 2
                if text_y > self.height - self.base_font_height * 2:
                    text_y = self.base_font_height
                    parts.append(lines)
                    lines = []
            else:
                words = i_line.replace(NNBSP, NBSP).split(' ')
                i = 0
                while i < len(words):
                    line = ''
                    while i < len(words) and self.font.getsize(line + words[i])[0] <= self._max_width:
                        line = line + words[i] + " "
                        i += 1
                    if not line:
                        line = words[i]
                        i += 1

                    lines.append(line)
                    text_y += self.base_font_height + 2
                    if text_y > self.height - self.base_font_height * 2:
                        text_y = self.base_font_height
                        parts.append(lines)
                        lines = []

        parts.append(lines)

        return parts

    def render(self, text: str, typo: bool, part: int):
        """Render image"""
        part = self.split_text(text, typo)[part]

        self._reset_line()
        for line in part:
            self._draw_line(line)
        return self.image
