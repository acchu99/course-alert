import os
import json
import time
import urllib
import requests
import schedule
from trycourier import Courier
from dotenv import load_dotenv

load_dotenv()

TARGET_MAIL=os.getenv("TARGET_MAIL")
COURIER_API_KEY=os.getenv("COURIER_API_KEY")
COURIER_TEMPLATE_ID=os.getenv("COURIER_TEMPLATE_ID")
TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")


class Alert:
    def __init__(self, class_id) -> None:
        self.URL="https://eadvs-cscc-catalog-api.apps.asu.edu/catalog-microservices/api/v1/search/classes"
        self.headers = {
            "authorization": "Bearer null",
            "origin": "https://catalog.apps.asu.edu",
            "referer": "https://catalog.apps.asu.edu/",
        }
        self.class_id = class_id
    
    @staticmethod
    def send_gmail_notification(data):
        client = Courier(auth_token=COURIER_API_KEY)

        _ = client.send_message(
        message={
            "to": {
                "email": "acchu99@gmail.com"
            },
            "template": COURIER_TEMPLATE_ID,
            "data": {
                "course": data['course'],
                "instructor": data['instructor'],
                "seats": data['seats'],
                "add": data['add'],
                "swap": data['swap'],
            },
        }
        )

    @staticmethod
    def send_telegram_notification(telegram_text):
        telegram_token = TELEGRAM_TOKEN
        telegram_chat_id = TELEGRAM_CHAT_ID
        text = urllib.parse.quote_plus(telegram_text)
        url = f'https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={telegram_chat_id}&text={text}'
        _ = requests.get(url, timeout=10)

    def check_seats(self):
        querystring = {
            "refine":"Y",
            "campusOrOnlineSelection":"A",
            "keywords":self.class_id,
            "searchType":"all",
            "term":"2241"
        }

        out = requests.get(
            self.URL, 
            data="", 
            headers=self.headers, 
            params=querystring
        ).json()['classes'][0]

        seats = out['seatInfo']['ENRL_CAP']-out['seatInfo']['ENRL_TOT']
        class_title = out['CLAS']['COURSETITLELONG']
        class_term = out['CLAS']['STRM']
        class_instructor = out['CLAS']['INSTRUCTORSLIST'][0]

        add_link = f"https://go.oasis.asu.edu/addclass/?STRM={class_term}&ASU_CLASS_NBR={self.class_id}"
        swap_link = f"https://webapp4.asu.edu/myasu/?action=swapclass&strm={class_term}"
        
        if seats > 0:
            # print(logger(class_title, class_instructor, seats, add_link, swap_link))
            self.send_telegram_notification(logger(class_title, class_instructor, seats, add_link, swap_link))
            self.send_gmail_notification(logger(class_title, class_instructor, seats, add_link, swap_link, False))


def load_courses():
    with open("./courses.json", "r") as f:
        data = json.load(f)
    return data['courses']


def logger(course_name, instructor, seats, add_link, swap_link, telegram=True):
    if telegram:
        return f"COURSE ALERT!!!\n\n{course_name} by {instructor} is available with {seats} seats\n\nGRAB IT NOW!\n\nADD TO CART: {add_link}\n\nOR\n\nSWAP: {swap_link}"
    else:
        return {
            "course": course_name,
            "instructor": instructor,
            "seats": seats,
            "add": add_link,
            "swap": swap_link
        }

def main():
    alerts = [Alert(course) for course in load_courses()]
    for alert in alerts:
        alert.check_seats()

if __name__=="__main__":
    # runs main() every one minute
    schedule.every(1).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
