import requests
import urllib3
from transitions import Machine

TOKEN = 'bot5044928682:AAFj973a8wHgxGtNX4UNc4rUb3uWBW8MNJQ'
timer = None


class Order:
    def __init__(self, size, payment):
        self.size = size
        self.payment = payment


pay = Order(None, None)

states = ['start', 'size', 'pay_type', 'confirm', 'end']

transitions = [
    {'trigger': 'to_start', 'source': 'end', 'dest': 'start'},
    {'trigger': 'to_size', 'source': 'start', 'dest': 'size'},
    {'trigger': 'to_pay', 'source': 'size', 'dest': 'pay_type'},
    {'trigger': 'to_confirm', 'source': 'pay_type', 'dest': 'confirm'},
    {'trigger': 'to_end', 'source': 'confirm', 'dest': 'end'}
]

machine = Machine(pay, states=states, transitions=transitions, initial='start')


def get_updates(offset=0, timeout=300, allowed_updates=None) -> dict:
    value = {'offset': offset, 'timeout': timeout, 'allowed_updates': allowed_updates}
    response = requests.get(f'https://api.telegram.org/{TOKEN}/getUpdates', params=value)
    response_json = response.json()['result']
    return response_json[-1]


def send_message(cid, text) -> requests.models.Response:
    value = {'chat_id': cid, 'text': text}
    response = requests.post(f'https://api.telegram.org/{TOKEN}/sendMessage', data=value)
    return response


if __name__ == '__main__':
    while True:
        try:
            last_update = get_updates(timer)
            question = last_update['message']['text']

            # send_message(last_update['message']['chat']['id'], question)

            """Каждый диалог можно перенести в отдельный метод и управлять диалогом только при помощи состояний"""

            print(f'До: {pay.state}')

            if question == 'Новый заказ':
                pay.state = 'start'

            if pay.state == 'start':
                pay.to_size()
                send_message(last_update['message']['chat']['id'], 'Какую вы хотите пиццу? "Большая"/"Маленькая"')
            elif pay.state == 'size' and (question == 'Большая' or question == 'Маленькая'):
                pay.to_pay()
                pay.size = question
                send_message(last_update['message']['chat']['id'], 'Как вы будете оплачивать? "Карта"/"Наличные"')
            elif pay.state == 'pay_type' and (question == 'Карта' or question == 'Наличные'):
                pay.to_confirm()
                pay.payment = question
                send_message(last_update['message']['chat']['id'],
                             f'Ваш заказ: Пицца - {pay.size} Оплата - {pay.payment}? "Да"/"Нет"')
            elif pay.state == 'confirm':
                if question == 'Да':
                    pay.to_end()
                    send_message(last_update['message']['chat']['id'], 'Спасибо за заказ!')
                elif question == 'Нет':
                    pay.to_end()
                    send_message(last_update['message']['chat']['id'], 'Сделаем новый заказ?')

            print(f'После: {pay.state}')

            timer = last_update['update_id'] + 1
        except (IndexError, TimeoutError, KeyboardInterrupt, KeyError, urllib3.exceptions.NewConnectionError,
                urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
            ...
