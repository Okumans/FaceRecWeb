import shelve
import shutil
import warnings
import google_auth_httplib2
import firebase_admin
from firebase_admin import credentials, db, storage
import os.path as path
import numpy as np
import cv2
from PIL import Image, ImageOps
from io import BytesIO
import time
import requests
from datetime import timedelta
from typing import *


def check_internet():
    try:
        requests.get("http://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False


class DataBase:
    default = ("", "", "", 0, "", 0, 0, 0, [])

    class Storage:
        def __init__(self, cache=None):
            self.bucket = storage.bucket()
            self.internet = check_internet()
            self.cache: str = cache

        def add_image(self, ID, filename, resize):
            if path.exists(filename):
                with BytesIO() as f:
                    img = Image.open(filename)
                    img = ImageOps.contain(img, resize)
                    if self.cache is not None:
                        img.save(self.cache + f"/{ID}.png", format="png")
                    img.save(f, format="png")
                    img = f.getvalue()


                self.bucket.blob(ID).upload_from_string(img, content_type="image/png")
                
        def add_image_data(self, ID, data, resize):
                with BytesIO() as f:
                    img = Image.fromarray(data)
                    img = ImageOps.contain(img, resize)
                    if self.cache is not None:
                        img.save(self.cache + f"/{ID}.png", format="png")
                    img.save(f, format="png")
                    img = f.getvalue()
                self.bucket.blob(ID).upload_from_string(img, content_type="image/png")

        def exists(self, ID):
            return self.bucket.get_blob(ID) is not None

        def get_image(self, ID):
            if self.cache is not None and path.exists(self.cache + f"/{ID}.png"):
                return cv2.imread(self.cache + f"/{ID}.png")

            if self.internet:
                blob = self.bucket.get_blob(ID)
                if blob is None or blob is False:
                    return
                image = cv2.imdecode(np.frombuffer(blob.download_as_string(), np.uint8), cv2.COLOR_BGRA2BGR)
                cv2.imwrite(self.cache + f"/{ID}.png", image)
                return image
            else:
                return cv2.imread(path.dirname(__file__) + r"\resources\image_error.png")

        def smart_get_image(self, ID):
            if self.cache is not None:
                if path.exists(self.cache + f"/{ID}_HIGHRES.png"):
                    print("yee")
                    return cv2.imread(self.cache + f"/{ID}_HIGHRES.png")
                if path.exists(self.cache + f"/{ID}.png"):
                    return cv2.imread(self.cache + f"/{ID}.png")
            return self.get_image(ID)

        def get_cache_image(self, ID):
            if self.cache is not None:
                if path.exists(self.cache + f"/{ID}_HIGHRES.png"):
                    return cv2.imread(self.cache + f"/{ID}_HIGHRES.png")
                if path.exists(self.cache + f"/{ID}.png"):
                    return cv2.imread(self.cache + f"/{ID}.png")
            return None

        def get_image_link(self, ID):
            return self.bucket.blob(ID).generate_signed_url(timedelta(seconds=300), method='GET')
        
        def add_encoding(self, ID, encoding: str):
            self.bucket.blob("encoded/" + ID).upload_from_string(encoding.encode(encoding="unicode_escape"), content_type="application/octet-stream")

        def add_encoding_file(self, ID, filename):
            self.bucket.blob("encoded/" + ID).upload_from_filename(filename)

        def get_encoding(self, ID):
            if self.internet:
                blob = self.bucket.get_blob("encoded/" + ID)
                if blob is None or blob is False:
                    return
                data = blob.download_as_string()
                return data
        
        def delete(self, IDD):
            self.bucket.delete_blob(IDD)

        def delete_encoding(self, IDD):
            self.bucket.delete_blob("encoded/" + IDD)

    @staticmethod
    def check_certificate(certificate_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(certificate_path)
            firebase_admin.initialize_app(
                cred,
                {
                    "databaseURL": "https://facerec-24eea-default-rtdb.asia-southeast1.firebasedatabase.app",
                    "storageBucket": "facerec-24eea.appspot.com",
                },
            )

    def __init__(self, database_name, sync_with_offline_db=False, certificate_path="src/resources/serviceAccountKey.json"):
        self.check_certificate(certificate_path)

        self.db_name = database_name
        self.sync_with_offline_db: bool = sync_with_offline_db
        self.offline_db_folder_path = ""
        self.ref = db.reference(self.db_name)

    def latest_update_is_online(self):
        if self.sync_with_offline_db:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                offline = off_db.get("last_update")
                offline = 0 if offline is None else offline
                online = self.get_data("last_update")
                online = 0 if online is None else online
                if online == offline:
                    return None
                return online > offline
        else:
            return True

    def get_database(self):
        if self.sync_with_offline_db:
            try:
                return self.ref.get()
            except google_auth_httplib2.exceptions.TransportError:
                with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                    return dict(off_db)
        else:
            return self.ref.get()
        
    def get_students(self) -> Dict[str, Any]:
        db_dict = self.get_database()
        return {idd: db_dict[idd] for idd in db_dict if idd != "last_update"}


    def set_database(self, data):
        update_time = time.time()
        if self.sync_with_offline_db:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                try:
                    self.ref.set(data)
                    self.ref.child("last_update").set(update_time)
                except google_auth_httplib2.exceptions.TransportError:
                    for i in off_db:
                        del off_db[i]
                    for i in data:
                        off_db[i] = data[i]
                off_db["last_update"] = update_time
        else:
            self.ref.set(data)
            self.ref.child("last_update").set(update_time)

    def can_connect(self) -> bool:
        try:
            self.ref.get()
            return True
        except google_auth_httplib2.exceptions.TransportError:
            return False

    def add_data(
        self,
        ID: str,
        realname: str,
        surname: str,
        nickname: str,
        student_id: int,
        student_class: str,
        class_number: int,
        active_days: int,
        last_checked: int,
        graph_info: list,
        **kwargs
    ):
        # update database
        print(f"database add {ID}.")
        data = {
            ID: {
                "realname": realname,
                "surname": surname,
                "nickname": nickname,
                "student_id": student_id,
                "student_class": student_class,
                "class_number": class_number,
                "active_days": active_days,
                "last_checked": last_checked,
                "graph_info": graph_info,
                "last_update": 0,
                **kwargs,
            }
        }
        update_time = time.time()
        if self.sync_with_offline_db:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                for key, values in data.items():
                    try:
                        self.ref.child(key).set(values)
                        off_db[key] = values
                        self.ref.child("last_update").set(update_time)
                    except google_auth_httplib2.exceptions.TransportError:
                        off_db[key] = values
                off_db["last_update"] = update_time

        else:
            for key, values in data.items():
                self.ref.child(key).set(values)
            self.ref.child("last_update").set(update_time)

    def quick_get_data(self, ID: str) -> dict:
        if not self.sync_with_offline_db:
            warnings.warn("sync_with_offline_db is not turned on.")
            return self.ref.child(ID).get()
        else:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                return off_db.get(ID)

    def get_data(self, ID: str) -> dict:
        try:
            return self.ref.child(ID).get()
        except google_auth_httplib2.exceptions.TransportError:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                return off_db.get(ID)

    def get(self, ID: str) -> firebase_admin.db.Reference:
        return self.ref.child(ID)

    def update(self, ID: str, **data):
        update_time = time.time()
        if self.sync_with_offline_db:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                try:
                    values = self.get_data(ID)
                    for key, value in data.items():
                        values[key] = value
                    self.ref.child(ID).update(values)
                    off_db[ID] = values
                    self.ref.child("last_update").set(update_time)

                except google_auth_httplib2.exceptions.TransportError:
                    values = off_db[ID]
                    for key, value in data.items():
                        values[key] = value
                    off_db[ID] = values

                off_db["last_update"] = update_time
        else:
            values = self.get_data(ID)
            print(values)
            for key, value in data.items():
                values[key] = value
            self.ref.child(ID).update(values)
            self.ref.child("last_update").set(update_time)

    def delete(self, ID):
        print(f"database deleted {ID}.")
        update_time = time.time()
        if self.sync_with_offline_db:
            with shelve.open(self.offline_db_folder_path + "/" + self.db_name) as off_db:
                try:
                    self.ref.child(ID).delete()
                    try:
                        del off_db[ID]
                    except KeyError:
                        pass
                    self.ref.child("last_update").set(update_time)
                except google_auth_httplib2.exceptions.TransportError:
                    try:
                        del off_db[ID]
                    except KeyError:
                        pass
                off_db["last_update"] = update_time
        else:
            self.ref.child(ID).delete()
            self.ref.child("last_update").set(update_time)


if __name__ == "__main__":
    database = DataBase("Students")
    database.offline_db_folder_path = r"C:\general\Science_project\Science_project_cp39\resources_test_2"
    print(database.can_connect())
