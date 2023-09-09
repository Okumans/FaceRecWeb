import pickle
import face_recognition
import sys
import ray
import os.path as path
import cv2
import tabulate
from copy import deepcopy
import unicodedata as ud
import src.general_lite

files = sys.argv[1:]


def spilt_chunk(length, splitedSize):
    k, m = divmod(len(length), splitedSize)
    return [length[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(splitedSize)]


def split_chunks_of(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def resize_by_height(img, height):
    h, w, _ = img.shape
    img = cv2.resize(img, (0, 0), fx=height / h, fy=height / h)
    return img


@ray.remote
def process_image(info, resize_size_y=200):
    face_encodings = []
    for img in info:
        print(f"now processing..")
        face_location = face_recognition.face_locations(img)

        if len(face_location) > 1 or len(face_location) == 0:
            print("cannot contain more than one face." f"skipping..")
            return

        print(face_location)
        face_location = face_location[0]
        top, right, bottom, left = face_location
        face_encoding = face_recognition.face_encodings(
            resize_by_height(deepcopy(img[top:bottom, left:right]), resize_size_y)
        )
        if face_encoding:
            face_encodings.append(face_encoding)

    return face_encodings


def noMn(msg):
    return "".join(cp for cp in msg if ud.category(cp)[0] != "M")


if __name__ == "__main__":
    ray.init()
    allowed_extensions = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]
    cores = 8
    return_values = src.general_lite.rayDict.remote()
    print(
        tabulate.tabulate(
            list(
                zip(
                    range(len(files)),
                    map(lambda x: noMn(path.basename(x)), files),
                    map(lambda x: f"{round(path.getsize(x) / 1080)} kb", files),
                )
            ),
            headers=["No.", "Filenames", "Size"],
            tablefmt="fancy_grid",
        )
    )
    ID = input("please enter id: ")

    data = []
    for file in files:
        if not path.exists(file):
            continue
        data.append(cv2.cvtColor(cv2.imread(file), cv2.COLOR_BGR2RGB))

    a = []
    for chunk in spilt_chunk(data, cores):
        a.append(process_image.remote(chunk))

    result = []
    for i in ray.get(a):
        if i:
            result.append(i[0])

    print(len(result), type(result))
    for i in result:
        print(str(i)[:10])

    with open(f"{ID}.pkl", "wb") as f:
        pickle.dump({"id": ID, "data": result}, f)
    print("finished..")
