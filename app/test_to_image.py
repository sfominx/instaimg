from PIL import ImageFont, Image, ImageDraw
from typus import ru_typus
from typus.chars import NNBSP, NBSP

IMG_MODE = 'RGB'


class TextToImages:
    def __init__(self, width: int, height: int, font: ImageFont, background_color):
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

    def _reset_line(self):
        self._text_y = self.base_font_height
        self.image = Image.new(IMG_MODE, (self.width, self.height), color=self.background_color)
        self._canvas = ImageDraw.Draw(self.image)
        self._canvas.font = self.font
        self._new_image = True

    def _shift_line(self):
        self._new_image = False
        self._text_y += self.base_font_height + 2

    def _draw_line(self, text):
        self._canvas.text((self.base_font_width, self._text_y), text, fill=(0, 0, 0))
        if text.strip() or not self._new_image:
            self._shift_line()

    def split_text(self, text: str, typo: bool = True):
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
        part = self.split_text(text, typo)[part]

        self._reset_line()
        for line in part:
            self._draw_line(line)
        return self.image
