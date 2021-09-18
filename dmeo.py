import requests


def find_district(pin_code):
    name = []
    url = f'https://api.postalpincode.in/pincode/{pin_code}'
    data = requests.get(url.format(pin_code))
    if data.json()[0]['Status']:
        for i in data.json()[0]['PostOffice']:
            name.append(i['Name'])
    print(name)


if __name__ == '__main__':
    find_district('110094')
