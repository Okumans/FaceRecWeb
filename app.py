from flask import Flask, render_template, Response, jsonify, send_file
from markupsafe import escape
from typing import *
from copy import deepcopy
from datetime import datetime, timedelta
from itertools import islice
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from io import BytesIO
from base64 import b64encode, decodebytes
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os.path
import os
import uuid
import json
import re
from dataclasses import dataclass
from src.DataBase import DataBase
from src.attendant_graph import Arrange, AttendantGraph
from src.studentSorter import Student, StudentSorter
from src.FaceTrainer_server import QueueTrainer, Queue
from src.PdfGenerator import PdfTable
from src.leaderboard import LeaderBoard
# from src.FaceTrainer_server import VideoFaceTrainer

app = Flask(__name__)

UPLOAD_FOLDER = "recieved\images"
ALLOWED_EXTENSTIONS = ('.png', '.jpg', '.jpeg', '.gif', '.mp4')

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def make_safe_filename(filename):
    return "".join([c for c in filename if re.match(r'\w', c)])


def chunks(data, SIZE=50):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k: data[k] for k in islice(it, SIZE)}


def generate_profile(
    name: str, image_source: str = "static/images/unknown_people.png"
) -> np.ndarray:
    img = Image.open(image_source).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("Kanit-Medium.ttf", 50)
    name = name[:2]
    offset_x = font.getlength(name)
    height, width = img.height, img.width
    draw.text(
        (int(width / 2 - (offset_x / 2)), height // 2 - 55),
        name,
        (203, 203, 203),
        font=font,
    )
    buffered = BytesIO()

    img.save(buffered, format="PNG")
    img.resize((86, 86))

    return "data:image/png;base64," + b64encode(buffered.getvalue()).decode("ascii")


def load_raw_data(page: int) -> tuple[dict, int]:
    raw_data: dict = db.get_database()
    del raw_data["last_update"]
    raw_data = list(chunks(raw_data, SIZE=page_capacity))
    page = min(len(raw_data) - 1, page)
    raw_data = raw_data[page]
    return raw_data


def class_index(_db: DataBase = None, _db_dict: Dict = None) -> List[str]:
    if _db is None and _db_dict is None:
        return
    if _db_dict is not None:
        db_dict = _db_dict
    else:
        db_dict = _db.get_database()
        del db_dict["last_update"]

    classes: set[str] = set()
    student_idd: str
    for student_idd in db_dict:
        classes.add(db_dict[student_idd][Student.STUDENT_CLASS])
    return list(classes)


def process_raw_data(raw_data, image_links, check_state):
    for key in raw_data:
        raw_data[key]["realname"] = (
            key if not raw_data[key][Student.FIRSTNAME] else raw_data[key][Student.FIRSTNAME]
        )

        raw_data[key]["realname"] = raw_data[key]["realname"][:20]

        student = Student().load_from_dict(key, raw_data[key])

        check_state[key] = student.status(LATETIME)

        last_checked: datetime = datetime.fromtimestamp(
            raw_data[key][Student.LAST_CHECKED])
        if last_checked == datetime.fromtimestamp(0):
            raw_data[key][Student.LAST_CHECKED] = "Never checked."
        elif Arrange.same_day(last_checked, datetime.now()):
            raw_data[key][Student.LAST_CHECKED] = last_checked.strftime(
                "%H:%M:%S")
        elif Arrange.same_week(last_checked, datetime.now()):
            raw_data[key][Student.LAST_CHECKED] = last_checked.strftime(
                "%a %H:%M")
        else:
            raw_data[key][Student.LAST_CHECKED] = last_checked.strftime(
                "%d %b %y")

        if image_exists.get(key, False):
            image_links[key] = db_storage.get_image_link(key)
        else:
            image_links[key] = generate_profile(key)


def allow_extension(filename) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSTIONS


@app.route("/")
def index():
    return render_template("home.jinja")


@app.route("/names/<int:page>")
def information_name(page):
    SORTED_BY = 'name'
    raw_data = load_raw_data(page)
    raw_data = dict(
        sorted(
            raw_data.items(),
            key=lambda a: a[1].get(Student.FIRSTNAME)
            if a[1].get(Student.FIRSTNAME) != 0
            else "𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈",
        )
    )
    image_links: dict[str, str] = {}
    check_state: dict[str, bool] = {}

    process_raw_data(raw_data=raw_data,
                     image_links=image_links,
                     check_state=check_state
                     )

    return render_template(
        "page.jinja",
        data=raw_data,
        page_number=page,
        image_links=image_links,
        check_state=check_state,
        sorted_by=SORTED_BY
    )


@app.route('/downloaddoc/<page>/<subpage>')
def downloadFile(page, subpage):
    db_dict: Dict[str] = db.get_database()
    student_class = f"{page}/{subpage}"
    ss: StudentSorter = StudentSorter(data=db_dict, late_checked_hour_minute=LATETIME)
    class_students: List[str] = ss.sort_as_classes().get().get(student_class)
    students: List[Tuple[str, str, str, str]] = []
    for student_idd in class_students:
        student: Student = Student().load_from_dict(student_idd, db_dict.get(student_idd))
        students.append((student.student_class_number,
                         student.student_id,
                         student.realname,
                         student.status(LATETIME)))

    pdf: PdfTable = PdfTable(
            header=("เลขที่", "เลขประจำตัวนักเรียน", "ชื่อ - นามสกุล", "สถานะ"),
            data=students,
            column_ratio=(0.7, 2.7, 6, 2),
            column_align=('C', 'C', 'L', 'C'),
            output_filename=os.path.dirname(__file__) + "/" + CACHE_PATH+make_safe_filename("/result_"+student_class+".pdf"),
            student_class=student_class,
            student_program="วิทย์-คณิต",
            font_path=os.path.dirname(__file__) + "/" + "static/font/THSarabunNew.ttf",
            font_path_bold=os.path.dirname(__file__) + "/" + "static/font/THSarabunNew Bold.ttf",
            logo_image_path=os.path.dirname(__file__) + "/" + "static/images/scius.png"
            )
    
    pdf_file: BytesIO = pdf.get_pdf_bytes().getvalue()
    

    return send_file(
        BytesIO(pdf_file),
        download_name="result_"+make_safe_filename(student_class)+".pdf",
        as_attachment=True
    )

    
    

@app.route("/class-attendance-data/<page>")
def information_class_get(page):
    db_dict: Dict = db.get_database()
    del db_dict["last_update"]

    checked_count: Dict[str, int] = {}
    checked_late_count: Dict[str, int] = {}
    not_checked_count: Dict[str, int] = {}

    for idd in db_dict:
        if db_dict[idd][Student.STUDENT_CLASS].split("/")[0] == page:
            student: Student = Student().load_from_dict(idd, db_dict[idd])
            subclass = student.student_class.split("/")[1]

            if checked_count.get(subclass) is None:
                checked_count[subclass] = 0

            if checked_late_count.get(subclass) is None:
                checked_late_count[subclass] = 0

            if not_checked_count.get(subclass) is None:
                not_checked_count[subclass] = 0

            status: str = student.status(LATETIME)
            if status == Student.CHECKED:
                checked_count[subclass] += 1

            elif status == Student.CHECKED_LATE:
                checked_late_count[subclass] += 1

            elif status == Student.NOT_CHECKED:
                not_checked_count[subclass] += 1

    return jsonify({"checkedCount": checked_count,
                    "checkedLateCount": checked_late_count,
                    "notCheckedCount": not_checked_count})

@app.route("/classes")
def information_classes():
    db_dict: Dict = db.get_database()
    del db_dict["last_update"]
    classes_major: List[str] = [c.split("/")[0] for c in class_index(_db_dict=db_dict)]
    return render_template("not_found.jinja", header="Class list", subheader="these are valid class:", items=list(set(classes_major)), page="")
    

@app.route("/classes/<page>")
def information_class(page):
    db_dict: Dict = db.get_database()
    del db_dict["last_update"]
    classes_major: List[str] = [c.split("/")[0] for c in class_index(_db_dict=db_dict)]
    if page not in classes_major: 
        return render_template("not_found.jinja", header="Class not found!", subheader="these are valid class:", items=list(set(classes_major)), page="")
    return render_template("class_attendance.jinja")

@app.route("/classes/<page>/<subpage>")
def information_class_subclass(page, subpage):
    db_dict: Dict = db.get_database()
    valid_class: List[str] = []
    del db_dict["last_update"]
    for c in class_index(_db_dict=db_dict):
        if c.split("/")[0] == page and len(c.split("/")) == 2:
            valid_class.append(c.split("/")[1])
    if subpage in valid_class:
        return render_template("subclass_attendance.jinja")
    else:
        return render_template("not_found.jinja", header="Subclass not found!", subheader="these are valid class:", items=valid_class, page=page+"/")

@app.route("/subclass-attendance-data/<page>/<subpage>")
def information_class_subclass_get(page, subpage):

    db_dict: Dict = db.get_database()
    students_in_class: List[Student] = Student.from_idds(StudentSorter(data=db_dict).sort_as_classes().get().get(f"{page}/{subpage}", None), db_dict)
    
    attendance_data = []
    for student in students_in_class:
        data = Arrange(student.student_attendant_graph_data).arrange_in_day()
        if data:
            earliest: datetime = data[list(data)[0]][0]
            attendance_data.append({"student": student.to_dict(), 
                                    "checked": True,
                                    "time": earliest.timestamp(),
                                    "late": student.status(LATETIME) == Student.CHECKED_LATE})
        else:
            attendance_data.append({"student": student.to_dict(),
                                    "checked": False,
                                    "late" :True,
                                    "time": 0})
        attendance_data.sort(key=lambda a: int(a["student"][student.STUDENT_CLASS_NUMBER]) if a["student"][student.STUDENT_CLASS_NUMBER] != "0" else "zzzz")
    return jsonify({'attendanceData': attendance_data})


@app.route("/students_id/<int:page>")
def information_student_id(page):
    SORTED_BY = 'student number'
    raw_data: dict = load_raw_data(page)
    raw_data = dict(
        sorted(
            raw_data.items(),
            key=lambda a: int(a[1].get("student_id"))
            if int(a[1].get("student_id")) != 0
            else 999999
        )
    )
    print(raw_data, 'sdfsdfsdfdsfsdfds')
    image_links: dict[str, str] = {}
    check_state: dict[str, bool] = {}

    process_raw_data(raw_data=raw_data,
                     image_links=image_links,
                     check_state=check_state
                     )

    return render_template(
        "page.jinja",
        data=raw_data,
        page_number=page,
        image_links=image_links,
        check_state=check_state,
        sorted_by=SORTED_BY
    )


@app.route("/nicknames/<int:page>")
def information_nickname(page):
    SORTED_BY = 'nickname'
    raw_data: dict = load_raw_data(page)
    raw_data = dict(
        sorted(
            raw_data.items(),
            key=lambda a: a[1].get("nickname")
            if a[1].get("nickname") != 0
            else "𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈𐍈",
            reverse=True,
        )
    )
    image_links: dict[str, str] = {}
    check_state: dict[str, bool] = {}

    process_raw_data(raw_data=raw_data,
                     image_links=image_links,
                     check_state=check_state
                     )

    return render_template(
        "page.jinja",
        data=raw_data,
        page_number=page,
        image_links=image_links,
        check_state=check_state,
        sorted_by=SORTED_BY
    )


@app.route("/idd/<int:page>")
def information_IDD(page):
    SORTED_BY = 'IDD'
    raw_data: dict = load_raw_data(page)
    raw_data = dict(sorted(raw_data.items()))
    image_links: dict[str, str] = {}
    check_state: dict[str, bool] = {}

    process_raw_data(raw_data=raw_data,
                     image_links=image_links,
                     check_state=check_state
                     )

    return render_template(
        "page.jinja",
        data=raw_data,
        page_number=page,
        image_links=image_links,
        check_state=check_state,
        sorted_by=SORTED_BY
    )


@app.route("/latest/<int:page>")
def information_latest_check(page):
    SORTED_BY = 'latest checked'
    raw_data: dict = load_raw_data(page)
    raw_data = dict(
        sorted(
            raw_data.items(),
            key=lambda a: a[1].get('last_checked'),
            reverse=True
        )
    )

    image_links: dict[str, str] = {}
    check_state: dict[str, bool] = {}

    process_raw_data(raw_data=raw_data,
                     image_links=image_links,
                     check_state=check_state
                     )

    return render_template(
        "page.jinja",
        data=raw_data,
        page_number=page,
        image_links=image_links,
        check_state=check_state,
        sorted_by=SORTED_BY
    )


@app.route("/createidentity")
def create_identity():
    return render_template("new.jinja")


@app.route("/upload", methods=["POST"])
def upload():
    idd = uuid.uuid4().hex
    file = request.files["file"]
    personal_information = json.loads(request.form["PersonalInformation"])
    profile = request.form["profile"]
    print("upload", len(personal_information), len(profile), idd), bool(file)
    save_dir = os.path.join(app.config['UPLOAD_FOLDER'], idd)
    print(personal_information)
    os.mkdir(save_dir)

    if file:
        print(file)
        filename = secure_filename(file.filename)
        file.save(os.path.join(save_dir, filename))

        student: Student = Student().load_from_dict(idd, personal_information)
        print(student.show_table())
        qt.push(student)

        queueId: Union[Queue.QueueProperties, None] = qt.queue.get_by_index(-1)
        queueId = qt.inprocess.queueId if queueId is None and qt.inprocess.queueId is not None \
            else queueId.queueId if queueId is not None else "-"
        return queueId


@app.route("/capture", methods=["POST"])
def capture():
    idd = uuid.uuid4().hex
    data = request.get_json()
    data_urls = data['images']
    personal_information = data["PersonalInformation"]
    profile = data["profile"]
    save_dir = os.path.join(app.config['UPLOAD_FOLDER'], idd)

    os.mkdir(save_dir)
    print(personal_information)
    for index, data_url in enumerate(data_urls):
        data_url = data_url.split('base64,')[1]
        image = Image.open(BytesIO(decodebytes(bytes(data_url, "utf-8"))))
        image.save(os.path.join(save_dir, f"{index}.png"))
    if profile:
        data_url = profile.split('base64,')[1]
        image = Image.open(BytesIO(decodebytes(bytes(data_url, "utf-8"))))
        image.save(os.path.join(save_dir, f"profile.png"))

    student: Student = Student().load_from_dict(idd, personal_information)
    print(student.show_table())
    qt.push(student, 
            lambda: (db_storage.add_image(idd, os.path.join(save_dir, "profile.png"), (86, 86)), 
                       db_storage.add_image(idd+"_HIGHRES", os.path.join(save_dir, "profile.png"), (360, 360))),
                       print("upload profile image successfull"))

    queueId: Union[Queue.QueueProperties, None] = qt.queue.get_by_index(-1)
    queueId = qt.inprocess.queueId if queueId is None and qt.inprocess.queueId is not None \
        else queueId.queueId if queueId is not None else "-"
    print(queueId)
    return queueId


@app.route("/queues/<queue_id>")
def queues_table(queue_id):
    queues: Queue = qt.queue
    table: List[tuple[int, str, Student, str]] = []

    inprocess_queue: Queue.QueueProperties = qt.inprocess
    if inprocess_queue is None:
        table = [("-", "-", "-", "-")]

    else:
        time_taken: timedelta = inprocess_queue.operation_time()
        time_taken_formated: str = ":".join(
            [str(int(i)).zfill(2) for i in divmod(time_taken.total_seconds(), 60)])

        table.append([
            inprocess_queue.queueIndex,
            inprocess_queue.queueId,
            inprocess_queue.student.firstname,
            time_taken_formated
        ])

        queue: Queue.QueueProperties
        for queue in queues.loop():
            time_taken = inprocess_queue.operation_time() + (queue.queueIndex -
                                                             inprocess_queue.queueIndex)*inprocess_queue.operation_time()
            time_taken_formated = ":".join(
                [str(int(i)).zfill(2) for i in divmod(time_taken.total_seconds(), 60)])
            table.append([
                queue.queueIndex,
                queue.queueId,
                queue.student.firstname,
                time_taken_formated
            ])
    print(table)
    return render_template('queue_table.jinja', data=table, queue_id=queue_id)

@app.route("/queues_get")
def get_queues_table():
    queues: Queue = qt.queue
    table: List[tuple[int, str, Student, str]] = []

    inprocess_queue: Queue.QueueProperties = qt.inprocess
    if inprocess_queue is None:
        table = [("-", "-", "-", "-")]

    else:
        time_taken: timedelta = inprocess_queue.operation_time()
        time_taken_formated: str = ":".join(
            [str(int(i)).zfill(2) for i in divmod(time_taken.total_seconds(), 60)])

        table.append([
            inprocess_queue.queueIndex,
            inprocess_queue.queueId,
            inprocess_queue.student.firstname,
            time_taken_formated
        ])

        queue: Queue.QueueProperties
        for queue in queues.loop():
            time_taken = inprocess_queue.operation_time() + (queue.queueIndex -
                                                             inprocess_queue.queueIndex)*inprocess_queue.operation_time()
            time_taken_formated = ":".join(
                [str(int(i)).zfill(2) for i in divmod(time_taken.total_seconds(), 60)])
            table.append([
                queue.queueIndex,
                queue.queueId,
                queue.student.firstname,
                time_taken_formated
            ])
    return jsonify({"data":table})


@app.route("/students/<student_idd>", methods=["GET"])
def student_info_render(student_idd):
    student: Student = Student().load_from_db(db, student_idd)
    profile_image: np.ndarray = db_storage.get_image_link(
        student_idd) if db_storage.exists(student_idd) else generate_profile(student_idd)
    return render_template("student.jinja", student=student, idd=student_idd, profile_image=profile_image)


@app.route("/students-get-data/<student_idd>", methods=["GET"])
def student_info_get(student_idd):
    student: Student = Student().load_from_db(db, student_idd)
    graph_data: list[datetime] = student._student_attendant_graph_data
    print(graph_data, "graphdata")

    graph_data_first_checked: list[float] = AttendantGraph(today=datetime.now()).load_datetimes(
        graph_data).data_in_month() if graph_data else []
    
    checked = Arrange(graph_data).arrange_in_all_as_day().get(
        (datetime.now().year, datetime.now().month, datetime.now().day),
        False)
    student_dict: Dict = student.to_dict()
    print(graph_data_first_checked)
    try:
        student_dict["graph_info"] = [
            list(graph_data_first_checked[0]), list(graph_data_first_checked[1])]
    except IndexError:
        student_dict["graph_info"] = []
    student_dict["checked"] = checked
    print(student_dict)
    return jsonify({"student": student_dict, "status": student.status(LATETIME)})

@app.route("/leaderboard/<int:page>")
def leaderboard(page):
    ldb: LeaderBoard = LeaderBoard(db)
    ranks = ldb.load_all_from_db().get_ranks()
    data = {}
    image_links = {}
    student_rank = {}

    ranks = list(chunks(ranks, SIZE=page_capacity))
    page = min(len(ranks) - 1, page)
    ranks = ranks[page]

    for ind, rank in enumerate(ranks):
        student_rank[rank] = (20*page) + ind+1
        if student_rank[rank] == 1:
            student_rank[rank] = "👑"
        elif student_rank[rank] == 2:
            student_rank[rank] = "🥈"
        elif student_rank[rank] == 3:
            student_rank[rank] = "🥉"
        cal_point: Tuple[int, int, int] = ldb.calculate_point(rank)
        data[rank] = {"student": db.get_data(rank),
                      "points": {"points": round(float(cal_point[0]), 2),
                                 "streak": cal_point[1],
                                 "days": cal_point[2]}}
        print(round(int(cal_point[0]), 3))
        if data[rank]["student"][Student.FIRSTNAME] + " " + data[rank]["student"][Student.LASTNAME] == " ":
            data[rank]["student"][Student.FIRSTNAME] = rank
        
        data[rank]["student"][Student.FIRSTNAME] = data[rank]["student"][Student.FIRSTNAME][:20]
        if image_exists.get(rank, False):
            image_links[rank] = db_storage.get_image_link(rank)
        else:
            image_links[rank] = generate_profile(rank)

    return render_template(
        "leaderboard.jinja",
        data=data,
        image_links=image_links,
        page_number = 0,
        rank=student_rank
    )

if __name__ == "__main__":
    CACHE_PATH = "cache"

    USED_FOLDER: list[str] = ["db", "trained", CACHE_PATH, "recieved", "recieved/images"]
    # create used folder.
    for use_folder in USED_FOLDER:
        if not os.path.exists(use_folder):
            os.mkdir(use_folder)

    LATETIME = (9, 0, 0)

    db: DataBase = DataBase("Students", certificate_path="serviceAccountKey.json", sync_with_offline_db=True)
    db.offline_db_folder_path = "db"
    db_storage: DataBase.Storage = db.Storage(cache=CACHE_PATH)
    image_exists: dict[str, bool] = {}
    page_capacity = 20
    qt: QueueTrainer = QueueTrainer(
        input_path="recieved/images", output_path="trained", db=db, cache_path=CACHE_PATH)
    qt.core = 3
    
    for key in db.get_database():
        print("indexing.", key, end="")
        if key.startswith("unknown:"):
            image_exists[key] = False
        else:
            image_exists[key] = db_storage.exists(key)
        if image_exists[key]:
            print(" exists")
        else:
            print(" not exists")

    # print(generate_profile("heeloo"))
    app.run(debug=True, port=5000, host="0.0.0.0")
