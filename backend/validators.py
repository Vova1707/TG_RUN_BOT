import re
import datetime




def check_time(time):
    pattern = r'^([01]\d|2[0-3]):([0-5]\d)$'
    exe = {
        not time: 'Поле не может быть пустым',
        not re.match(pattern, time): 'Некорректное время'
    }
    for ex in exe:
        if ex:
            return exe[ex]
    return True


def check_date(date):
    pattern = r'^\d{2}.\d{2}.\d{4}$'
    if not re.match(pattern, date):
        return "Ошибка"

    try:
        date_obj = datetime.datetime.strptime(date, '%d.%m.%Y')
    except ValueError:
        return 'Некорректная дата'

    today = datetime.datetime.today()
    if date_obj < today:
        return 'Дата не может быть в прошлом'
    if date_obj > today + datetime.timedelta(days=365):
        return 'Дата не может быть в будущем'

    return True

def check_description(description):
    exe = {
        not description: 'Поле не может быть пустым',
        len(description) > 3000: 'Слишком длинное описание'
    }
    for ex in exe:
        if ex:
            return exe[ex]
    return True


def check_distance_km(distance):
    try:
        distance = float(distance)
    except ValueError:
        return 'Некорректное расстояние'
    exe = {
        not distance: 'Поле не может быть пустым.',
        float(distance) < 0: 'Расстояние не может быть отрицательным и быть равным нулю.'
    }
    for ex in exe:
        if ex:
            return exe[ex]
    return True