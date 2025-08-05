import requests
import polyline

# Координаты (Москва, Кремль -> Красная площадь)
start_lon, start_lat = 37.617635, 55.752023
end_lon, end_lat = 37.621900, 55.753700

# 1. Получаем маршрут от OSRM
osrm_url = f"http://router.project-osrm.org/route/v1/foot/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full"
route_data = requests.get(osrm_url).json()

# 2. Декодируем полилинию
coords = polyline.decode(route_data["routes"][0]["geometry"], 6)

# 3. Формируем ссылку на интерактивные Яндекс.Карты
yandex_maps_url = (
    f"https://yandex.ru/maps/?mode=routes"
    f"&rtext={start_lat}%2C{start_lon}~{end_lat}%2C{end_lon}"
    f"&rtt=pd"  # пешеходный маршрут
    f"&ruri=~"  # добавляем все промежуточные точки
)

# Добавляем все точки маршрута (кодируем в polyline)
for lat, lon in coords[::5]:  # берем каждую 5-ю точку
    yandex_maps_url += f"~{lat}%2C{lon}"

print("Ссылка на интерактивный маршрут в Яндекс.Картах:")
print(yandex_maps_url)