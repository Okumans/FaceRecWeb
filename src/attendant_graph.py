from random import randrange
from datetime import timedelta, datetime, timezone
from typing import Dict, Tuple, Any
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Arrange:
    def __init__(self, dates: list[datetime] = None, today: datetime = None):
        self.dates: list[datetime] = [] if dates is None else dates
        self.today: datetime = datetime.now() if today is None else today

    @staticmethod
    def same_hour(date1: datetime, date2: datetime):
        return (
            date1.hour == date2.hour
            and date1.day == date2.day
            and date1.month == date2.month
            and date1.year == date2.year
        )

    @staticmethod
    def same_day(date1: datetime, date2: datetime):
        return (
            date1.day == date2.day
            and date1.month == date2.month
            and date1.year == date2.year
        )

    @staticmethod
    def same_week(date1: datetime, date2: datetime):
        return (
            date1.isocalendar()[1] == date2.isocalendar()[1]
            and date1.year == date2.year
        )

    @staticmethod
    def same_month(date1: datetime, date2: datetime):
        return date1.month == date2.month and date1.year == date2.year

    @staticmethod
    def same_year(date1: datetime, date2: datetime):
        return date1.year == date2.year

    def add_date(self, date: datetime):
        self.dates.append(date)

    def arrange_in_day(self, today: datetime = None) -> dict[datetime]:
        today = self.today if today is None else today
        result = {}
        for date in self.dates:
            if self.same_day(today, date):
                result[date.hour] = result.get(date.hour, []) + [date]
        return result

    def arrange_in_week(self, today: datetime = None) -> dict[datetime]:
        today = self.today if today is None else today
        result = {}
        for date in self.dates:
            if self.same_week(today, date):
                result[date.isocalendar()[2]] = result.get(
                    date.isocalendar()[2], []
                ) + [date]
        return result

    def arrange_in_month(self, today: datetime = None) -> dict[datetime]:
        today = self.today if today is None else today
        result = {}
        for date in self.dates:
            if self.same_month(today, date):
                result[date.month] = result.get(date.month, []) + [date]
        return result

    def arrange_in_month_as_day(self, today: datetime = None) -> dict[datetime]:
        today = self.today if today is None else today
        result = {}
        for date in self.dates:
            if self.same_month(today, date):
                result[date.day] = result.get(date.day, []) + [date]
        return result

    def arrange_in_year_as_day(self, today: datetime = None) -> dict[datetime]:
        today = self.today if today is None else today
        result = {}
        for date in self.dates:
            if self.same_year(today, date):
                print(date.month, date.year)
                result[(date.month, date.day)] = result.get(
                    (date.month, date.day), []
                ) + [date]
        return result

    def arrange_in_all_as_day(
        self, today: datetime = None
    ) -> dict[tuple[int, int], Any]:
        today = self.today if today is None else today
        result = {}
        for date in self.dates:
            result[(date.year, date.month, date.day)] = result.get(
                (date.year, date.month, date.day), []
            ) + [date]
        return result

    @staticmethod
    def get_hour_minute(times: list[datetime]) -> list[datetime]:
        result = []
        for time in times:
            result.append(datetime(2000, 1, 1, time.hour, time.minute, time.second))
        return result

    @staticmethod
    def get_day(times: list[datetime]) -> list[datetime]:
        result = []
        for time in times:
            result.append(datetime(2000, 1, time.day))
        return result

    @staticmethod
    def get_month_day(times: list[datetime]) -> list[datetime]:
        result = []
        for time in times:
            result.append(datetime(2000, time.month, time.day))
        return result


class AttendantGraph:
    def __init__(self, today: datetime = None):
        self.today: datetime = datetime.now() if today is None else today
        self.dates: list[datetime] = []

    def load_float(self, time: float):
        self.dates.append(datetime.fromtimestamp(time))
        return self

    def load_floats(self, times: list[float]):
        for time in times:
            self.dates.append(datetime.fromtimestamp(time))
        return self

    def load_string(self, time: str, time_format: str = "%c"):
        self.dates.append(datetime.strptime(time, time_format))
        return self

    def load_strings(self, times: list[str], time_format: str = "%c"):
        for time in times:
            self.dates.append(datetime.strptime(time, time_format))
        return self

    def load_datetime(self, time: datetime):
        self.dates.append(time)
        return self

    def load_datetimes(self, times: list[datetime]):
        for time in times:
            self.dates.append(time)
        return self

    def data_in_week(self) -> tuple[list[float], list[float]]:
        data = Arrange(self.dates)
        data_processed = data.arrange_in_week(today=self.today)
        most_early_check_valur_raw = Arrange.get_hour_minute(
            list(map(min, data_processed.values()))
        )
        first_day_of_week = datetime.today() - timedelta(days=self.today.isoweekday())
        most_early_check_key = Arrange.get_day(
            [
                first_day_of_week + timedelta(days=i)
                for i in range(len(most_early_check_valur_raw))
            ]
        )

        if most_early_check_key and most_early_check_valur_raw:
            most_early_check_key, most_early_check_valur_raw = zip(
                *sorted(zip(most_early_check_key, most_early_check_valur_raw))
            )
            return most_early_check_key, most_early_check_valur_raw
        else:
            return [], []

    def data_in_month(self) -> tuple[list[float], list[float]]:
        dates = Arrange(self.dates)
        data_processed = dates.arrange_in_month_as_day(today=self.today)

        most_early_check_valur_raw = Arrange.get_hour_minute(
            list(map(min, data_processed.values()))
        )
        most_early_check_key = Arrange.get_day(
            [
                datetime.now() + timedelta(days=i)
                for i in range(len(most_early_check_valur_raw))
            ]
        )

        if most_early_check_valur_raw and most_early_check_key:
            most_early_check_key, most_early_check_valur_raw = zip(
                *sorted(zip(most_early_check_key, most_early_check_valur_raw))
            )
            return most_early_check_key, most_early_check_valur_raw
        else:
            return [], []

    def data_in_year(self) -> tuple[list[float], list[float]]:
        dates = Arrange(self.dates)
        data_processed = dates.arrange_in_year_as_day(today=self.today)
        most_early_check_valur_raw = Arrange.get_hour_minute(
            list(map(min, data_processed.values()))
        )
        most_early_check_key = Arrange.get_month_day(
            [
                datetime(datetime.now().year, 1, 1) + timedelta(days=i)
                for i in range(len(most_early_check_valur_raw))
            ]
        )

        if most_early_check_valur_raw and most_early_check_key:
            most_early_check_key, most_early_check_valur_raw = zip(
                *sorted(zip(most_early_check_key, most_early_check_valur_raw))
            )
            return most_early_check_key, most_early_check_valur_raw
        return [], []

    @staticmethod
    def show(
        key_data: list[float],
        value_data: list[float],
        x_label: str = None,
        y_label: str = None,
    ):
        x_label = "Dates" if x_label is None else x_label
        y_label = "Time" if y_label is None else y_label
        fig, ax = plt.subplots()
        ax.yaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))

        df = pd.DataFrame()
        df["Date"] = key_data
        df["Time"] = value_data
        pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S.%f")
        pd.to_datetime(df["Time"], format="%Y-%m-%d %H:%M:%S.%f")
        df.set_index(df["Date"], inplace=True)
        ax.plot(df.index, df.Time, color="blue")
        ax.fill_between(df.index, df.Time, color="blue")
        plt.gcf().autofmt_xdate()
        plt.axhline(y=np.nanmean(value_data))
        plt.xlabel(x_label)
        plt.xlabel(y_label)
        plt.show()


if __name__ == "__main__":
    # def random_date(start, end):
    #     delta = end - start
    #     int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    #     random_second = randrange(int_delta)
    #     return start + timedelta(seconds=random_second)
    #
    #
    # data = []
    # for j in range(12):
    #     for i in range(28):
    #         data.append(random_date(
    #             datetime.strptime(f'{j+1}/{i + 1}/2022 6:30 AM', '%m/%d/%Y %I:%M %p'),
    #             datetime.strptime(f'{j+1}/{i + 1}/2022 6:30 PM', '%m/%d/%Y %I:%M %p'))
    #         )
    from DataBase import DataBase

    db = DataBase("Students")
    data = db.get_data("17c07c286703416cbda35579cf998f68")["graph_info"]
    print(data)
    AttendantGraph.show(
        *AttendantGraph(today=datetime.today()).load_floats(data).data_in_week()
    )
    print(AttendantGraph(today=datetime.today()).load_floats(data).data_in_week())
