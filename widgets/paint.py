from enum import Enum

from kivy.graphics import Color, Line, Rectangle
from kivy.uix.widget import Widget

from networking.networkthread import NETWORK_INTERFACE


class DrawingMode(Enum):
    DRAW = 1
    ERASE = 2


BLACK_COLOR = (0, 0, 0, 1)


#

class ColorPickerObject(Widget):
    def set_color(self, color):
        self.ids["color_picker"].color = color


class PaintingMode(Widget):
    # def on_touchmove(self, touch):
    #     print(self.size)
    #     sizeOfFieldX = self.size[0] / self.xSize
    #     sizeOfFieldY = self.size[1] / self.ySize
    #     x, y = touch.pos
    #     rectpos = int(x / sizeOfFieldX) * sizeOfFieldX, int(y / sizeOfFieldY) * sizeOfFieldY
    #     with self.canvas:
    #         Color(1, 0, 0)
    #         Rectangle(pos=rectpos, size=(sizeOfFieldX, sizeOfFieldY))

    def drawLines(self):
        root = self.ids["print_area"]
        sizeOfFieldX = root.size[0] / self.xSize
        sizeOfFieldY = (root.size[1]) / self.ySize

    def drawRectange(self, pos_color_tuple):
        (x, y), (r, g, b, _) = pos_color_tuple

        root = self.ids["print_area"]
        sizeOfFieldX = root.size[0] / self.xSize
        sizeOfFieldY = root.size[1] / self.ySize
        with root.canvas:
            rect_pos = x * sizeOfFieldX, y * sizeOfFieldY
            Color(r, g, b)
            Rectangle(pos=rect_pos, size=(sizeOfFieldX, sizeOfFieldY))

    def redraw(self):
        root = self.ids["print_area"]
        sizeOfFieldX = root.size[0] / self.xSize
        sizeOfFieldY = root.size[1] / self.ySize
        last_index = len(self.drawing_history) - self.end_index

        if not self.live_draw:
            if self.end_index != 0:
                self.ids["next_arrow"].opacity = 1
            else:
                self.ids["next_arrow"].opacity = 0.1
            if len(self.drawing_history) != 0 and last_index != 0:
                self.ids["prev_arrow"].opacity = 1
            else:
                self.ids["prev_arrow"].opacity = 0.1

        if self.mode == DrawingMode.DRAW:
            self.ids["pen_button"].opacity = 1
            self.ids["eraser_button"].opacity = 0.1
        elif self.mode == DrawingMode.ERASE:
            self.ids["pen_button"].opacity = 0.1
            self.ids["eraser_button"].opacity = 1

        with root.canvas:
            root.canvas.clear()
            # for x in range(0, int(root.size[0])-1, int(sizeOfFieldX)):

            for i, ((x, y), (r, g, b, a)) in enumerate(self.drawing_history):
                if i == last_index:
                    break
                rect_pos = x * sizeOfFieldX, y * sizeOfFieldY
                Color(r, g, b)
                Rectangle(pos=rect_pos, size=(sizeOfFieldX, sizeOfFieldY))
            Color(1, 1, 0)
            for x in range(0, self.xSize):
                for y in range(0, self.ySize):
                    # for y in range(0, int(root.size[1])-1, int(sizeOfFieldY)):
                    Line(rectangle=[x * sizeOfFieldX, y * sizeOfFieldY, sizeOfFieldX, sizeOfFieldY], width=1)

    def add_to_history(self, t):
        if any(item == t for item in self.drawing_history):
            return
        # if len(self.drawing_history) != 0 and self.drawing_history[-1] == tuple:
        #     return
        if self.end_index != 0:
            self.drawing_history = self.drawing_history[:-self.end_index]
            self.end_index = 0
        self.drawing_history.append(t)
        self.drawRectange(t)
        if self.live_draw:
            NETWORK_INTERFACE.pixel_draw(t, self.screen_id, self.ySize)

    def erase_all(self):
        self.drawing_history.clear()
        self.end_index = 0
        if self.live_draw:
            NETWORK_INTERFACE.clear_display(self.screen_id)
        self.redraw()

    def erase(self, rect_pos):
        # self.drawing_history = list(filter(lambda pos: pos[0] != rect_pos, self.drawing_history))
        self.add_to_history((rect_pos, BLACK_COLOR))

    def widget_touch_event(self, root, x, y, button):
        sizeOfFieldX = root.size[0] / self.xSize
        sizeOfFieldY = root.size[1] / self.ySize
        rect_pos = int(x / sizeOfFieldX), int(y / sizeOfFieldY)
        r, g, b, a = self.color
        color_to_draw = (r, g, b, a)
        if button == "right":
            if self.mode == DrawingMode.DRAW:
                self.erase(rect_pos)
            elif self.mode == DrawingMode.ERASE:
                self.add_to_history((rect_pos, color_to_draw))
        elif button == "left":
            if self.mode == DrawingMode.DRAW:
                self.add_to_history((rect_pos, color_to_draw))
            elif self.mode == DrawingMode.ERASE:
                self.erase(rect_pos)
        #self.redraw()

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        root = self.ids["print_area"]
        x, y = touch.pos
        if 'button' in touch.profile:
            button = touch.button
        else:
            button = "left"
        if root.collide_point(x, y):
            self.widget_touch_event(root, x, y, button)

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        root = self.ids["print_area"]
        x, y = touch.pos
        if 'button' in touch.profile:
            button = touch.button
        else:
            button = "left"
        if root.collide_point(x, y):
            self.widget_touch_event(root, x, y, button)

    def on_touch_up(self, touch):
        self.redraw()

    def on_resize(self):
        # with self.ids["print_area"].canvas:
        #     Color(1, 0, 0)
        #     Rectangle(pos=(0, 0), size = (100, 100))
        self.redraw()

    def back_arrow(self):
        if not self.live_draw:
            if len(self.drawing_history) != 0 and len(self.drawing_history) - self.end_index != 0:
                self.end_index += 1
            self.redraw()

    def forward_arrow(self):
        if not self.live_draw:
            if self.end_index != 0:
                self.end_index -= 1
            self.redraw()

    def pen_click(self):
        self.mode = DrawingMode.DRAW
        self.redraw()

    def eraser_click(self):
        self.mode = DrawingMode.ERASE
        self.redraw()

    def on_open(self, clear_all):
        if clear_all:
            self.erase_all()


    def __init__(self, x, y, screen_id=0, live_draw=True, **kwargs):
        super().__init__(**kwargs)
        self.xSize = x
        self.ySize = y
        self.drawing_history = []
        self.end_index = 0
        self.color = (1, 0, 0, 1)
        self.mode = DrawingMode.DRAW
        self.live_draw = live_draw
        self.screen_id = screen_id

