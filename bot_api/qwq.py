import requests
from bs4 import BeautifulSoup

# Получаем информацию об организации
url = "http://static-maps.yandex.ru/1.x/?geocode=Москва,+ул.+Ленина,+1&filter=site:shop&lang=ru"
response = requests.get(url)
print(response.content)
#soup = BeautifulSoup(response.content, features='xml')
'''
# Получаем сайт магазина
site = soup.find('a', {'class': 'site'})['href']

# Парсим сайт магазина
response = requests.get(site)
soup = BeautifulSoup(response.content, 'html.parser')

# Получаем информацию о товарах и ценах
products = soup.find_all('div', {'class': 'product'})
for product in products:
    print(product)
    '''