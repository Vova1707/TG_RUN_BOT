import requests
import polyline
import random
import math
from geopy.distance import geodesic
from bot_api.test import get_route_distance


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



