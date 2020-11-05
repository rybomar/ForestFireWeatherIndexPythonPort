import datetime

class DatesSelector:
    selectedDays = []

    def __init__(self):
        self.selectedDays = []

    def getLatestNotCalculatedDays(self):
        return self.selectedDays

