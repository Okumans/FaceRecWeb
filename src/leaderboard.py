from src.DataBase import DataBase
from src.studentSorter import Student
from src.attendant_graph import Arrange, AttendantGraph
from typing import *
from datetime import datetime
from dataclasses import dataclass

class Earliest:
    def __init__(self, students_by_time: Dict[str, datetime] = None):
        self.students_by_time: Dict[str, datetime] = students_by_time if students_by_time is not None else {}
        self.sort()

    def sort(self):
        student_by_time: List[Tuple[str, datetime]] = list(self.students_by_time.items())
        sorted_student_by_time: List[Tuple[str, datetime]] = sorted(student_by_time, key=lambda item: item[1])
        sorted_student_by_time_dict: Dict[str, datetime] = {item[0]:item[1] for item in sorted_student_by_time}
        self.students_by_time = sorted_student_by_time_dict
        return self

    def add(self, IDD: str, earliest: datetime):
        self.students_by_time.update({IDD: earliest})
        self.sort()
    
    def earliest(self) -> List[str]:
        return list(self.students_by_time.keys())

class LeaderBoard:
    TOP_RANK_POINTS = {
        1: 4,
        2: 3.75,
        3: 3.5,
        4: 3,
        5: 2.75,
        6: 2.5,
        7: 2.25,
        8: 2,
        9: 1.75,
        10: 1.5
    }

    def __init__(self, db: DataBase, students: List[Student] = None, late_time: Tuple[int, int, int] = None):
        self.db: DataBase = db
        self.students: List[Student] = students if students is not None else []
        self.late_time: Tuple[int, int, int] = late_time if late_time is not None else (8, 0, 0)
    
    def load_all_from_db(self):
        db_dict = self.db.get_students()
        students: List[Student] = [Student().load_from_dict(student, db_dict[student]) for student in db_dict]  
        self.students.extend(students)
        return self
    
    def day_ranks(self) -> Dict[Tuple[int, int, int], List[datetime]]:
        people_earliest_each_day: Dict[Tuple[int, int, int], Earliest] = {}
        for student in self.students:
            all_checks: Dict[Tuple[int, int, int], List[datetime]] = Arrange(student.student_attendant_graph_data).arrange_in_all_as_day()
            for day in all_checks:
                day_checks: List[Dict[datetime, Any]] = Arrange(all_checks[day]).arrange_in_day(today=datetime(year=day[0],
                                                                                                               month=day[1],
                                                                                                               day=day[2],
                                                                                                               hour=0,
                                                                                                               minute=0,
                                                                                                               second=0))
                if day_checks:
                    earliest: datetime = day_checks[list(day_checks)[0]][0]
                    if people_earliest_each_day.get(day) is None:
                        people_earliest_each_day[day] = Earliest()
                    people_earliest_each_day[day].add(student.IDD, earliest)
        return {day: people_earliest_each_day[day].earliest() for day in people_earliest_each_day}

    def student_rank(self, IDD: str) -> Dict[Tuple[int, int, int], int]:
        day_ranks: Dict[Tuple[int, int, int], List[datetime]] = self.day_ranks()
        student_rank: Dict[Tuple[int, int, int], int] = {}
        for day in day_ranks:
            try:
                student_rank[day] = day_ranks[day].index(IDD) + 1
            except ValueError:
                student_rank[day] = None
        return student_rank

    def student_ranks(self) -> Dict[str, Dict[Tuple[int, int, int], int]]:
        student_ranks: Dict[str, Dict[Tuple[int, int, int], int]] = {}
        for student in self.db.get_students().keys():
            student_ranks[student] = self.student_rank(student)
        return student_ranks
            

    def process(self):
        for student in self.students:
            all_checks: Dict[Tuple[int, int, int], List[datetime]] = Arrange(student.student_attendant_graph_data).arrange_in_all_as_day()
            for day in all_checks:
                day_checks: List[Dict[datetime, Any]] = Arrange(all_checks[day]).arrange_in_day()
                if day_checks:
                    earliest: datetime = day_checks[list(day_checks)[0]][0]
                    if earliest < datetime(day[0],
                                            day[1],
                                            day[2],
                                            self.late_time[0],
                                            self.late_time[1],
                                            self.late_time[2]):
                        return self.CHECKED
                    else:
                        return self.CHECKED_LATE
                else:
                    return self.NOT_CHECKED
        return self
    
    def status_in(self, student: Student, year: int, month: int, day: int):
        all_checks: Dict[Tuple[int, int, int], List[datetime]] = Arrange(student.student_attendant_graph_data).arrange_in_all_as_day()
        if all_checks.get((year, month, day)) is None:
            return None
        else:
            day_checks: List[Dict[datetime, Any]] = Arrange(all_checks[(year, month, day)]).arrange_in_day()
            if day_checks:
                earliest: datetime = day_checks[list(day_checks)[0]][0]
                if earliest < datetime(year,
                                        month,
                                        day,
                                        self.late_time[0],
                                        self.late_time[1],
                                        self.late_time[2]):
                    return Student.CHECKED
                else:
                    return Student.CHECKED_LATE
            else:
                return Student.NOT_CHECKED



    def calculate_point(self, IDD: str):
        student: Student = Student().load_from_dict(IDD, self.db.get_data(IDD))
        student_rank: Dict[Tuple[int, int, int], int] = self.student_rank(IDD)
        days = 0
        streak = 0
        points = 0
        for day in student_rank: # can generate bug if there's no one attended.
            if student_rank[day] is None:
                streak = 0
                points -= 1
            elif self.status_in(student, *day) == Student.CHECKED_LATE:
                days += 1
                streak -= 5

                if student_rank[day] <= 10:
                    points += self.TOP_RANK_POINTS[student_rank[day]] * (1.005 + (streak * 0.005))
                else:
                    points += 1
            else:
                days += 1
                streak += 1

                if student_rank[day] <= 10:
                    points += self.TOP_RANK_POINTS[student_rank[day]] * (1.005 + (streak * 0.005))
                else:
                    points += 1
            
            if streak % 10 == 0:
                points += streak // 10 * 2

            if days % 10 == 0:
                points += 1+((days//10)*0.25)
        return points, streak, days

    def get_ranks(self):
        rank: Dict[str, float] = {student.IDD: self.calculate_point(student.IDD)[0] for student in self.students}
        sorted_rank: Tuple[str, float] = sorted(rank.items(), key=lambda item: item[1], reverse=True)
        sorted_rank_dict: Dict[str, float] = {item[0]: item[1] for item in sorted_rank}
        return sorted_rank_dict
        
        
                                                            
if __name__ == "__main__":
    db: DataBase = DataBase("Students", sync_with_offline_db=True, certificate_path="../serviceAccountKey.json")
    db.offline_db_folder_path = "../db"

    print(LeaderBoard(db).load_all_from_db())