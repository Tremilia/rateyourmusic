# standard library modules
import os, re
from time import time, sleep
from random import random
from collections import namedtuple
from urllib.parse import urlparse

# outside of standard library modules
from bs4 import BeautifulSoup

# project modules
from rateyourmusic.helpers import disk_memoize, safe_get, origin, data_dir

maxage=10**100

sonemic_dir = os.path.join(data_dir, 'sonemic')
rym_dir = os.path.join(sonemic_dir, 'rateyourmusic')
@disk_memoize(dn=rym_dir, encoding='utf-8', maxage=maxage)
def rym_save(**kw):
    import _auth.rateyourmusic_auth as auth
    old_credentials_message = f"Credentials are too old. You will get IP banned from rateyourmusic if you continue scraping. Update the cookies and headers in {auth.__file__} to continue."
    if time() - os.path.getmtime(auth.__file__) > 3600: raise Exception(old_credentials_message)

    random_wait_time = 5+10*random()
    # an attempt to confuse RYM firewall so you don't get banned

    print(f'sleeping for {random_wait_time:.1f} seconds')
    sleep(random_wait_time)
    return safe_get(kw['name'],
        headers=auth.headers, cookies=auth.cookies, must_be_ok=True).text

object_release_card = namedtuple('card', ['year','title','artist'])
def process_single_rym_page(soup):
    cards_in_this_page = []
    for tag in soup.find_all(class_='object_release'):
        if tag.name != 'div': continue
        
        date = tag\
            .find(class_='page_charts_section_charts_item_date')\
            .find('span').text
        year = re.search(r'(\d){4}', date)
        if year is not None: year = year.group(0)

        data = tag\
            .find(class_='page_charts_section_charts_item_media_links')\
            .find('div')
        
        cards_in_this_page.append( object_release_card(
            year = year,
            title = data['data-artists'],
            artist = data['data-albums'],
        ))
    return cards_in_this_page

def process_main_link(url):    
    all_cards = []
    while True:
        path = urlparse(url).path.strip('/').split('/')
        pagenumber = path.pop() if path[-1].isdigit() else 1
        subdirectory = os.path.join(*path)
        html = rym_save(name=url, sd=subdirectory, fn=f'{pagenumber}.html')
        soup = BeautifulSoup(html, 'lxml')

        cards_in_this_page = process_single_rym_page(soup)
        all_cards.extend(cards_in_this_page)
        for i,card in enumerate(cards_in_this_page):
            print(f'#{i+1 +40*(int(pagenumber)-1)}| {card.year}: {card.title} by {card.artist}')
        
        link = soup.find(class_='ui_pagination_next')
        if link is None or 'href' not in link.attrs: break
        href = link['href']
        url = origin(url)+href if href[0]=='/' else href