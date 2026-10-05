from datetime import datetime

def get_current_season() -> str:
    month = datetime.now().month
    if month in (6, 7, 8, 9):
        return "Kharif"
    elif month in (10, 11, 12, 1, 2, 3):
        return "Rabi"
    else:
        return "Zaid"
