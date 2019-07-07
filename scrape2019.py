from lxml.html import parse
import sqlite3
import re
import requests

conn = sqlite3.connect('shows.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS shows')
c.execute('DROP TABLE IF EXISTS runs')
c.execute('DROP TABLE IF EXISTS venues')
c.execute('CREATE TABLE venues (id integer PRIMARY KEY, name text, address text)')
c.execute('CREATE TABLE shows (id integer PRIMARY KEY, name text, url text, venue_id integer, genre text, length integer, FOREIGN KEY(venue_id) REFERENCES venues(id))')
c.execute('CREATE TABLE runs (show_id integer, day integer, hour integer, minute integer, FOREIGN KEY(show_id) REFERENCES shows(id))')

tree = parse('full2019.html').getroot()

all_shows = {}
venues = {}

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
    venue_info = page_content.cssselect('.venue-info')[0]
    venue = venue_info.cssselect('h3')[0].text_content()
    venue = ' '.join(venue.split(' ')[2:])
    venue_address_parent = venue_info.cssselect('address > p')[0]
    venue_address = ' '.join(venue_address_parent.itertext()).strip()
    print(venue_address)

    performances = page_content.cssselect('.performances tbody tr')
    showtimes = []
    for performance in performances:
        children = performance.getchildren()
        content = children[1].text_content() + ' ' + children[2].text_content()
        if content.endswith('*'):
            content = content[:-1]
        showtimes += [content]
    
    all_shows[title] = {
        'url': url,
        'venue': { 'name': venue, 'address': venue_address },
        'genre': None,
        'length': length,
        'showtimes': showtimes,
    }

for show in all_shows.values():
    venue = show['venue']
    if venue['name']  not in venues:
        c.execute('INSERT INTO venues(id, name, address) VALUES(NULL, ?, ?)', (venue['name'], venue['address']))
        venues[venue['name']] = c.lastrowid

for (title, show) in all_shows.items():
    c.execute('INSERT INTO shows(id, name, url, venue_id, genre, length) VALUES(NULL, ?, ?, ?, ?, ?)',
              (title, show['url'], venues[show['venue']['name']], show['genre'], show['length']))
    show_id = c.lastrowid

    for time in show['showtimes']:
        parts = time.split(' ')
        day = int(parts[0][:-2])
        hour = int(parts[2].split(':')[0])
        minute = int(parts[2].split(':')[1][0:-2])
        if parts[2][-2:] == 'pm' and hour != 12:
            hour += 12

        c.execute('INSERT INTO runs VALUES(?, ?, ?, ?)', (show_id, day, hour, minute))

conn.commit()

c.close()
