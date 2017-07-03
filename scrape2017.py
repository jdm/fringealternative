from lxml.html import parse
import sqlite3
import re
import requests

conn = sqlite3.connect('shows.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS shows')
c.execute('DROP TABLE IF EXISTS runs')
c.execute('CREATE TABLE shows (id integer PRIMARY KEY, name text, url text, venue text, genre text, length integer)')
c.execute('CREATE TABLE runs (show_id integer, day integer, hour integer, minute integer, FOREIGN KEY(show_id) REFERENCES shows(id))')

tree = parse('full2017.html').getroot()

all_shows = {}

shows = tree.cssselect('.show-card')
for show in shows:
    title = show.cssselect('h2')[0].text_content()
    print('Scraping %s' % title)
    link = show.cssselect('.more-link a')[0]

    url = 'https://fringetoronto.com' + link.get('href')
    show_info_content = requests.get(url)
    with open('tmp.html', 'w') as f:
        f.write(show_info_content.text.encode('utf-8'))
    page_content = parse('tmp.html').getroot()

    length = page_content.cssselect('.columns .right dd')[0].text_content()
    length_match = re.findall(r'\d+', length)
    if length_match:
        length = int(length_match[0])
    else:
        length = 0

    performances = page_content.cssselect('.performances')[0]
    show_info = performances.getprevious()
    venue = show_info.cssselect('h3')[0].text_content()

    performances = page_content.cssselect('.performances tbody tr')
    showtimes = []
    for performance in performances:
        children = performance.getchildren()
        showtimes += [children[0].text_content() + ' ' + children[1].text_content()]
    
    all_shows[title] = {
        'url': url,
        'venue': venue,
        'genre': None,
        'length': length,
        'showtimes': showtimes,
    }

for (title, show) in all_shows.items():
    c.execute('INSERT INTO shows(id, name, url, venue, genre, length) VALUES(NULL, ?, ?, ?, ?, ?)',
              (title, show['url'], show['venue'], show['genre'], show['length']))
    show_id = c.lastrowid

    for time in show['showtimes']:
        print(time)
        parts = time.split(' ')
        day = int(parts[0][:-2])
        hour = int(parts[2].split(':')[0])
        minute = int(parts[2].split(':')[1][0:-2])
        if parts[2][-2:] == 'pm' and hour != 12:
            hour += 12

        c.execute('INSERT INTO runs VALUES(?, ?, ?, ?)', (show_id, day, hour, minute))

conn.commit()

c.close()
