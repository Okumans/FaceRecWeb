"""
Filename: FaceAlignment.py
Author: Jeerabhat Supapinit
"""

import cv2 as cv
import numpy as np
from PIL import Image
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates


def face_alignment(img, detection):
    mp_face_detection = mp.solutions.face_detection
    if img.any():
        image_rows, image_cols, _ = img.shape
        eye_left = mp_face_detection.get_key_point(detection, mp_face_detection.FaceKeyPoint.LEFT_EYE)
        eye_right = mp_face_detection.get_key_point(detection, mp_face_detection.FaceKeyPoint.RIGHT_EYE)
        right_eye_position = _normalized_to_pixel_coordinates(eye_right.x, eye_right.y, image_cols, image_rows)
        left_eye_position = _normalized_to_pixel_coordinates(eye_left.x, eye_left.y, image_cols, image_rows)
        dY = right_eye_position[1] - left_eye_position[1]
        dX = right_eye_position[0] - left_eye_position[0]
        angle = np.degrees(np.arctan2(dY, dX)) - 180
        img = np.array(Image.fromarray(img).rotate(angle))

    return img
