import requests
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


'''
# Пример использования
url = 'https://yandex.ru/maps/?mode=routes&rtext=55.823585%2C38.825699~55.78952717437486%2C38.8967312542789&rtt=pd&ruri=~~5.58208%2C3.881993~5.582258%2C3.881717~5.582045%2C3.881417~5.581944%2C3.881588~5.581815%2C3.881936~5.581653%2C3.882408~5.581619%2C3.882566~5.581594%2C3.882766~5.581537%2C3.882817~5.581297%2C3.882925~5.581318%2C3.883244~5.581345%2C3.883527~5.581418%2C3.88432~5.581476%2C3.884972~5.581396%2C3.885141~5.580828%2C3.885439~5.580712%2C3.885556~5.58031%2C3.886375~5.580026%2C3.886956~5.579961%2C3.887223~5.579956%2C3.887399~5.579968%2C3.887664~5.579824%2C3.887895~5.579818%2C3.888106~5.579795%2C3.88825~5.579726%2C3.888392~5.579606%2C3.888552~5.57945%2C3.888771~5.579316%2C3.888876~5.579166%2C3.888996~5.579033%2C3.889112~5.57899%2C3.889238~5.578974%2C3.889483'

distance = get_route_distance(url)
if distance is not None:
    print(f"Расстояние маршрута: {distance} км")
'''
