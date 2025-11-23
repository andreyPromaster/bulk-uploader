from .interfaces import Store


class ListStore(Store):
    def __init__(self):
        self.acc = list()

    def add(self, chunck: dict):
        self.acc.append(chunck)

    def saved_data(self):
        return self.acc.copy()
