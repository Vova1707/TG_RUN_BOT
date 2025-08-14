import requests
import polyline
import random
import math
from geopy.distance import geodesic
from bs4 import BeautifulSoup
import re

def get_route_distance(url):
    try:
        # Отправляем GET-запрос
        response = requests.get(url)
        response.raise_for_status()  # Проверяем успешность запроса
        print(response)
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        distance_text = soup.find(string=re.compile(r'(\d+\.?\d*)\s*км.*'))
        print(distance_text)
        if distance_text:
            # Извлекаем числовое значение
            distance = distance_text
            print(distance_text)
            return float(distance.replace('км', '').strip().replace(',', '.'))
        else:
            print("Не удалось найти информацию о расстоянии")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None
    except ValueError as ve:
        print(f"Ошибка преобразования в число: {ve}")
        return None




def set_path(start_coord, distance):
    start_lon, start_lat = start_coord

    # Генерируем рандомную точку на карте
    while True:
        random_angle = random.uniform(0, 2 * math.pi)
        random_distance = random.uniform(0, distance)
        end_lon = start_lon + random_distance * math.cos(random_angle) / geodesic((start_lat, start_lon), (start_lat, start_lon + 1)).meters
        end_lat = start_lat + random_distance * math.sin(random_angle) / geodesic((start_lat, start_lon), (start_lat + 1, start_lon)).meters

        # Проверяем, что координаты находятся в пределах допустимых значений
        if not (-180 <= end_lon <= 180) or not (-90 <= end_lat <= 90):
            continue

        # Проверяем расстояние между точками
        route_distance = geodesic((start_lat, start_lon), (end_lat, end_lon)).meters
        if route_distance <= distance + 500 and route_distance >= distance - 500:
            break

    # Получаем маршрут от OSRM
    osrm_url = f"http://router.project-osrm.org/route/v1/foot/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full"
    route_data = requests.get(osrm_url).json()

    # Проверяем наличие ключа 'routes' в словаре route_data
    if 'routes' not in route_data:
        print("Ошибка: ключ 'routes' не найден в ответе от OSRM")
        return None

    # Декодируем полилинию
    coords = polyline.decode(route_data["routes"][0]["geometry"], 6)

    # Формируем ссылку на интерактивные Яндекс.Карты
    yandex_maps_url = (
        f"https://yandex.ru/maps/?mode=routes"
        f"&rtext={start_lat}%2C{start_lon}~{end_lat}%2C{end_lon}"
        f"&rtt=pd"  # пешеходный маршрут
        f"&ruri=~"  # добавляем все промежуточные точки
    )

    # Добавляем все точки маршрута (кодируем в polyline)
    for lat, lon in coords[::5]:  # берем каждую 5-ю точку
        yandex_maps_url += f"~{lat}%2C{lon}"

    s = get_route_distance(yandex_maps_url)
    if s != None and abs(s * 1000 - distance) <= 500:
        print(s * 1000, distance, abs(s * 1000 - distance))
        print(yandex_maps_url)
        return yandex_maps_url
    try:
        print(s * 1000, distance, abs(s * 1000 - distance))
    except Exception as e:
        print(e)
    return None



'''
# Пример использования
url = 'https://yandex.ru/maps/?mode=routes&rtext=55.823585%2C38.825699~55.78952717437486%2C38.8967312542789&rtt=pd&ruri=~~5.58208%2C3.881993~5.582258%2C3.881717~5.582045%2C3.881417~5.581944%2C3.881588~5.581815%2C3.881936~5.581653%2C3.882408~5.581619%2C3.882566~5.581594%2C3.882766~5.581537%2C3.882817~5.581297%2C3.882925~5.581318%2C3.883244~5.581345%2C3.883527~5.581418%2C3.88432~5.581476%2C3.884972~5.581396%2C3.885141~5.580828%2C3.885439~5.580712%2C3.885556~5.58031%2C3.886375~5.580026%2C3.886956~5.579961%2C3.887223~5.579956%2C3.887399~5.579968%2C3.887664~5.579824%2C3.887895~5.579818%2C3.888106~5.579795%2C3.88825~5.579726%2C3.888392~5.579606%2C3.888552~5.57945%2C3.888771~5.579316%2C3.888876~5.579166%2C3.888996~5.579033%2C3.889112~5.57899%2C3.889238~5.578974%2C3.889483'

distance = get_route_distance(url)
if distance is not None:
    print(f"Расстояние маршрута: {distance} км")
'''