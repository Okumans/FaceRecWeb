from collections import OrderedDict


class topData:
    def __init__(self, max_size=10, min_detection=24):
        self.data = OrderedDict()
        self.max_size = max_size
        self.min_detection = min_detection

    def add_image(self, score, data):
        if len(self.data) >= self.max_size:
            self.data = OrderedDict(sorted(self.data.items(), reverse=True))
            if list(self.data.keys())[-1] < score:
                # print("min:", list(self.data.keys())[-1], "max:", list(self.data.keys())[0])
                self.data.popitem()

            else:
                return
        self.data.update({score: data})

    def add(self, key, data):
        if len(self.data.get(key, [])) >= self.max_size:
            self.data[key].pop(0)
        if self.data.get(key) is None:
            self.data[key] = [data]
        else:
            self.data[key].append(data)

    def amount(self):
        return len(self.data)

    def clear(self):
        self.data = OrderedDict()

    def lowest(self):
        if self.data.keys():
            return list(self.data.keys())[-1]
        else:
            return 0

    def highest(self):
        if self.data.keys():
            return list(self.data.keys())[0]
        else:
            return 0

    def is_full(self):
        return len(self.data) == self.max_size

    def get(self):
        return list(self.data.values())


class ListTopData:
    def __init__(self, max_size=10):
        self.data = []
        self.max_size = max_size

    def add(self, data):
        if len(self.data) >= self.max_size:
            self.data.pop(0)
        self.data.append(data)

    def amount(self):
        return len(self.data)

    def clear(self):
        self.data = []

    def is_full(self):
        return len(self.data) == self.max_size

    def top(self):
        return self.data[-1]

    def back(self):
        return self.data[0]

    def get(self):
        return self.data
