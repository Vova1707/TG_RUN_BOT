import random
import math
import requests
from geopy.distance import geodesic
import polyline

def get_route_distance(url):
    # Эта функция больше не нужна для получения расстояния,
    # но оставим её для отладки или если потребуется парсинг
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"Запрос к Яндекс.Картам успешен: {response.status_code}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Яндекс.Картам: {e}")
        return None

def set_path(start_coord, distance):
    start_lon, start_lat = start_coord

    # Максимальное количество попыток
    max_attempts = 50
    for _ in range(max_attempts):
        # Генерируем случайную точку на заданном расстоянии
        random_angle = random.uniform(0, 2 * math.pi)
        random_distance = random.uniform(distance - 500, distance + 500)  # В метрах

        # Вычисляем координаты конечной точки с помощью geopy
        start_point = (start_lat, start_lon)
        destination = geodesic(meters=random_distance).destination(start_point, random_angle)
        end_lat, end_lon = destination.latitude, destination.longitude

        # Проверяем, что координаты в допустимых пределах
        if not (-180 <= end_lon <= 180) or not (-90 <= end_lat <= 90):
            continue

        # Получаем маршрут от OSRM
        osrm_url = f"http://router.project-osrm.org/route/v1/foot/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full"
        try:
            response = requests.get(osrm_url)
            response.raise_for_status()
            route_data = response.json()

            # Проверяем наличие ключа 'routes'
            if 'routes' not in route_data or not route_data['routes']:
                print("Ошибка: ключ 'routes' не найден или маршрут пуст")
                continue

            # Получаем расстояние маршрута от OSRM (в метрах)
            route_distance = route_data["routes"][0]["distance"]
            print(f"Длина маршрута от OSRM: {route_distance} м, нужно +- 500 м {distance} м")

            # Проверяем, подходит ли расстояние
            if abs(route_distance - distance) <= 500:
                # Декодируем полилинию
                coords = polyline.decode(route_data["routes"][0]["geometry"], 6)

                # Формируем ссылку на Яндекс.Карты
                yandex_maps_url = (
                    f"https://yandex.ru/maps/?mode=routes"
                    f"&rtext={start_lat}%2C{start_lon}~{end_lat}%2C{end_lon}"
                    f"&rtt=pd"  # Пешеходный маршрут
                    f"&ruri=~"
                )

                # Добавляем промежуточные точки (каждую 5-ю)
                for lat, lon in coords[::5]:
                    yandex_maps_url += f"~{lat}%2C{lon}"

                print(f"Найден маршрут: {yandex_maps_url}")
                print(f"Расстояние: {route_distance} м, Цель: {distance} м, Разница: {abs(route_distance - distance)} м")
                return yandex_maps_url

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к OSRM: {e}")
            continue

    print(f"Не удалось найти маршрут с нужным расстоянием после {max_attempts} попыток")
    return None


'''
# Пример вызова
coord = (37.6173, 55.7558)  # Пример: координаты Москвы
distance = 5000  # 5 км в метрах
link = None
count = 0
max_tries = 50
while link is None and count < max_tries:
    link = set_path(coord, distance)
    count += 1
print(f"Итоговая ссылка: {link}")
'''