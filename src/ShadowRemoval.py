import cv2
import face_recognition
import sys
import cv2

from itertools import combinations_with_replacement
from collections import defaultdict

import numpy as np
from numpy.linalg import inv


def remove_shadow_grey(img):
    if img.any():
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        smooth = cv2.GaussianBlur(gray, (95, 95), 0)
        division = cv2.divide(gray, smooth, scale=192)
        return division
