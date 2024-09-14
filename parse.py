from bs4 import BeautifulSoup
import bs4
import requests

from typing import List, Dict, Set

import utils


def get_available_days(parser: BeautifulSoup) -> List[bs4.element.Tag]:
    days: List[str] = ['day' + str(i) for i in range(1, 8)]
    a_tags: List[bs4.element.Tag] = [parser.find('a', attrs={'name': day}) for day in days]

    return [tag.find_next('td', {'class': 'weekdaytitle'}) for tag in a_tags]


def get_correct_time(time_element: bs4.element.Tag, **kwargs) -> str:
    url = 'http://vsetv.com'

    images = time_element.find_all('img')

    if kwargs.get('mode') == 'manual':
        images_number_to_number: Dict[str, List[str]] = {
            '0': ['/pic/q4.gif', '/pic/l4.gif', '/pic/sh.gif', '/pic/ph.gif'],
            '5': ['/pic/wu.gif', '/pic/i2.gif', '/pic/ey.gif'],
        }
    else:
        urls_set: Set[str] = set(str(img['src']) for img in images)

        images_number_to_number: Dict[str, List[str]] = {
            utils.predict_number(str(url + image_url)): [image_url] for image_url in urls_set
        }

    for img in images:
        src = img['src']
        for number, img_src in images_number_to_number.items():
            if src in img_src:
                img.replace_with(number)

    time = time_element.get_text(strip=True)

    return time


def get_program_elements(program_day_tag: bs4.element.Tag) -> List[bs4.element.Tag]:
    tags: List[bs4.element.Tag] = []
    schedule_container: bs4.element.Tag = program_day_tag.find_next('div', {'id': 'schedule_container'})

    for _ in range(3):
        if schedule_container:
            tags.append(schedule_container)
            schedule_container = schedule_container.find_next('div', {'id': 'schedule_container'})
        else:
            break

    return tags


def get_program(elements: List[bs4.element.Tag]) -> List[str]:
    program: List[str] = []

    for el in elements:
        for time_div, program_div in zip(el.find_all('div', class_='time'), el.find_all('div', class_='prname2')):
            time_text = get_correct_time(time_div)
            program_text = program_div.get_text(strip=True)
            img_tag = program_div.find('img', src='pic/ico_live.gif')

            if img_tag:
                program.append(f"LIVE {time_text} - {program_text}")
            else:
                program.append(f"{time_text} - {program_text}")

    return program


def parse(website_url: str) -> BeautifulSoup:
    result: requests.models.Response = requests.get(website_url)
    content: str = result.text
    soup: BeautifulSoup = BeautifulSoup(content, 'lxml')

    return soup


if __name__ == '__main__':
    website = 'http://www.vsetv.com/schedule_channel_2027_week.html'
    soup_obj = parse(website)

    program_days = [utils.translate_text_to_ukrainian(program_day.get_text(strip=True))
                    for program_day in get_available_days(soup_obj)
                    ]

    tv_schedule = {
        program_day.get_text(strip=True): "\n".join(get_program(get_program_elements(program_day)))
        for program_day in get_available_days(soup_obj)
    }

    print(tv_schedule)
