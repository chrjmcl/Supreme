from bs4 import BeautifulSoup
import requests
import time

session = None

request = {
    'article': 'accessories',
    'keys': ['Speaker', '', ''],
    'color': '',
    'size': ''
}


def initialize():
    global session
    session = requests.session()


def get_items():
    global session
    endpoint = 'http://www.supremenewyork.com/shop/all/' + request['article']
    response = session.get(endpoint)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.findAll('div', {'class': 'inner-article'})


def monitor(items):
    global session
    while True:
        endpoint = 'http://www.supremenewyork.com/shop/all/' + request['article']
        response = session.get(endpoint)
        soup = BeautifulSoup(response.text, 'html.parser')
        items_refresh = soup.findAll('div', {'class': 'inner-article'})
        # should be if not
        if not items == items_refresh:
            print('Waiting on store update')
            time.sleep(2.5)
            monitor(items)
        else:
            return items_refresh


def find_item(items):
    global session
    for item in items:
        info = {
            'url': 'http://www.supremenewyork.com' + item.a['href'],
            'name': item.h1.text,
            'color': item.p.text
        }
        if request['color'] in info['color']:
            if request['keys'][0] in info['name']:
                    if request['keys'][1] in info['name']:
                        if request['keys'][2] in info['name']:
                            return info
    return 'Failed finding a matching item'


def get_item_page(item):
    global session
    response = session.get(item['url'])
    info = {
        'status_code': response.status_code,
        'soup': BeautifulSoup(response.text, 'html.parser')
    }
    return info


def add_to_cart(soup):
    global session
    if soup.find('b', {'class': 'button'}) is None:
        item_id = soup.find('form', {'class': 'add'})['action']
        if request['size'] in '':
            sizes = soup.findAll('option', {'': ''})
            if len(sizes) == 0:
                s = soup.find("input", {"name": "s"})["value"]
            else:
                for stock in sizes:
                    s = stock['value']
                    break
        else:
            sizes = soup.findAll('option', {'': ''})
            for stock in sizes:
                if request['size'] == stock.text:
                    s = stock['value']
                    break
                else:
                    s = -1
            if s == -1:
                info = {
                    'status_code': -1
                }
                return info
        endpoint = 'http://www.supremenewyork.com' + item_id
        data = {
            'utf8': soup.find("input", {"name": "utf8"})["value"],
            'st': soup.find("input", {"name": "st"})["value"],
            's': s,
            'commit': 'add to basket'
        }
        print(endpoint)
        print(data)
        print('')
        response = session.post(endpoint, data)
        info = {
            'status_code': response.status_code,
            'soup': soup
        }
        return info
    else:
        info = {
            'status_code': -1
        }
        return info


def get_checkout():
    global session
    endpoint = 'https://www.supremenewyork.com/checkout'
    response = session.get(endpoint)
    info = {
        'status_code': response.status_code,
        'soup': BeautifulSoup(response.text, 'html.parser')
    }
    return info


def checkout(soup):
    global session
    data = {
        'utf8': '✓',
        'authenticity_token': soup.find("input", {"name": "authenticity_token"})["value"],
        'order[billing_name]': 'FirstOO LastOO',
        'order[email]': 'Email@gmail.com',
        'order[tel]': '123-456-7890',
        'order[billing_address]': 'AddreOO',
        'order[billing_address_2]': 'APTO',
        'order[billing_zip]': '90210',
        'order[billing_city]': 'Beverly Hills',
        'order[billing_state]': 'CA',
        'order[billing_country]': 'USA',
        'asec': 'Rmasn',
        'same_as_billing_address': '1',
        'store_credit_id': '',
        'credit_card[nlb]': '2222 2222 2222 2222',
        'credit_card[month]': '22',
        'credit_card[year]': '2018',
        'credit_card[rvv]': '222',
        'order[terms]': '0',
        'order[terms]': '1'
    }
    endpoint = 'https://www.supremenewyork.com/checkout.json'
    response = session.post(endpoint, data)
    soup = BeautifulSoup(response.text, 'html.parser')
    info = {
        'status_code': response.status_code,
        'soup': soup
    }
    #print(soup)
    return info


def main():
    global session
    start = time.time()
    print('You are requesting to purchase:\n' + 'article: ' + request['article'] + '\nkeys: '
          + str(request['keys']) + '\ncolors: ' + request['color'] + '\nsize: '
          + request['size'] + '\n')

    initialize()
    item = get_items()
    item = find_item(monitor(item))

    print('An item has been found:\n' + 'url: ' + item['url'] + '\nname: ' + item['name']
          + '\ncolor: ' + item['color'] + '\n')

    code = get_item_page(item)
    while not code['status_code'] == 200:
        print('Failed to load ' + str(item['url']) + '\n')
        code = get_item_page(item)
    print('Successfully loaded ' + str(item['url']) + '\n')

    code = add_to_cart(code['soup'])
    while not code['status_code'] == 200:
        if code['status_code'] == -1:
            print('The item is out of stock')
            print("--- %s seconds ---" % (time.time() - start))
            return
        print('Failed to add ' + str(item['name']) + ' to the cart')
        code = add_to_cart(code['soup'])
    print('Successfully added ' + str(item['name']) + ' to the cart \n')

    code = get_checkout()
    while not code['status_code'] == 200:
        print('Failed to go to checkout')
        code = get_checkout()
    print('Successfully went to checkout\n')

    code = checkout(code['soup'])
    while not code['status_code'] == 200:
        print('Failed to checkout')
        code = checkout(code['soup'])
    print('Successfully checked out')
    print("--- %s seconds ---" % (time.time() - start))


main()
