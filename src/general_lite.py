"""
Filename: general.py
Author: Jeerabhat Supapinit
"""
from __future__ import annotations
import cv2
from typing import Callable, Tuple, Union
import time
import threading


def putBorderText(
    img,
    text,
    org,
    fontFace,
    fontScale,
    fg_color,
    bg_color,
    thickness,
    border_thickness=2,
    lineType=None,
    bottomLeftOrigin=None,
):
    cv2.putText(
        img=img,
        text=str(text),
        org=list(map(int, org)),
        fontFace=fontFace,
        fontScale=fontScale,
        color=bg_color,
        thickness=thickness + border_thickness,
        lineType=lineType,
        bottomLeftOrigin=bottomLeftOrigin,
    )
    cv2.putText(
        img=img,
        text=str(text),
        org=list(map(int, org)),
        fontFace=fontFace,
        fontScale=fontScale,
        color=fg_color,
        thickness=thickness,
        lineType=lineType,
        bottomLeftOrigin=bottomLeftOrigin,
    )


def get_from_percent(integer, percent, rounding=True):
    return round((percent / 100) * integer) if rounding else (percent / 100) * integer


def change_brightness(img, value=30):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.add(v, value)
    v[v > 255] = 255
    v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2RGB)
    return img


class Direction:
    Undefined = -1
    Up = 0
    Down = 1
    Left = 2
    Right = 3
    Forward = 4

    def __init__(self, degree_X_Y_Z: tuple[float], error_rate: Union[tuple[float], float] = None, name: str = None):
        self.degree_x: float = degree_X_Y_Z[0]
        self.degree_y: float = degree_X_Y_Z[1]
        self.degree_z: float = degree_X_Y_Z[2]
        self.name = "" if name is None else name

        error_rate = (0, 0, 0) if error_rate is None else error_rate
        if type(error_rate) == tuple:
            self.error_rate_x: float = error_rate[0]
            self.error_rate_y: float = error_rate[1]
            self.error_rate_z: float = error_rate[2]
        else:
            self.error_rate_x: float = error_rate
            self.error_rate_y: float = error_rate
            self.error_rate_z: float = error_rate

    def __hash__(self):
        return hash((self.degree_x, self.degree_y, self.degree_z))

    def __eq__(self, other):
        return (self.degree_x, self.degree_y, self.degree_z) == (other.degree_x, other.degree_y, other.degree_z)

    def maximum_error(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        max_error_left: Callable[[float], float] = (
            lambda degree, error_rate: degree * ((100 - error_rate) / 100) - error_rate / 10
        )
        max_error_right: Callable[[float], float] = (
            lambda degree, error_rate: degree * ((100 + error_rate) / 100) + error_rate / 10
        )

        return (
            (
                max_error_left(self.degree_x, self.error_rate_x),
                max_error_left(self.degree_y, self.error_rate_y),
                max_error_left(self.degree_z, self.error_rate_z),
            ),
            (
                max_error_right(self.degree_x, self.error_rate_x),
                max_error_right(self.degree_y, self.error_rate_y),
                max_error_right(self.degree_z, self.error_rate_z),
            ),
        )

    def direction(self) -> Tuple[float, float, float]:
        return self.degree_x, self.degree_y, self.degree_z

    def main_direction(self):
        degree_x = self.degree_x
        degree_y = self.degree_y
        degree_z = self.degree_z
        if degree_x >= degree_y and degree_x >= degree_z:
            return "x"
        if degree_y >= degree_x and degree_y >= degree_z:
            return "y"
        if degree_z >= degree_x and degree_z >= degree_y:
            return "z"

    def is_same(self, direction_: Direction) -> bool:
        max_error_left = (
            lambda degree, error_rate: (degree * ((100 - error_rate) / 100))
            + (-error_rate if degree > 0 else +error_rate) / 10
        )
        max_error_right = (
            lambda degree, error_rate: degree * ((100 + error_rate) / 100)
            + (error_rate if degree > 0 else -error_rate) / 10
        )
        min_x = min(max_error_left(self.degree_x, self.error_rate_x), max_error_right(self.degree_x, self.error_rate_x))
        max_x = max(max_error_left(self.degree_x, self.error_rate_x), max_error_right(self.degree_x, self.error_rate_x))
        min_y = min(max_error_left(self.degree_y, self.error_rate_y), max_error_right(self.degree_y, self.error_rate_y))
        max_y = max(max_error_left(self.degree_y, self.error_rate_y), max_error_right(self.degree_y, self.error_rate_y))
        min_z = min(max_error_left(self.degree_z, self.error_rate_z), max_error_right(self.degree_z, self.error_rate_z))
        max_z = max(max_error_left(self.degree_z, self.error_rate_z), max_error_right(self.degree_z, self.error_rate_z))
        print(min_x, max_x, min_y, max_y, min_z, max_z)
        if min_x <= direction_.degree_x <= max_x:
            if min_y <= direction_.degree_y <= max_y:
                if min_z <= direction_.degree_z <= max_z:
                    return True
        return False


class RepeatedTimer(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False