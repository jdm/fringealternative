from lxml.html import parse
import sqlite3
import re

conn = sqlite3.connect('shows.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS shows')
c.execute('DROP TABLE IF EXISTS runs')
c.execute('CREATE TABLE shows (id integer PRIMARY KEY, name text, url text, venue text, genre text, length integer)')
c.execute('CREATE TABLE runs (show_id integer, day integer, hour integer, minute integer, FOREIGN KEY(show_id) REFERENCES shows(id))')

tree = parse('full2016.html').getroot()

all_shows = {}

groups = tree.find_class('group')
for group in groups:
    shows = group.cssselect('div.show')
    datetime = group.cssselect('h2')[0].text_content()

    for show in shows:
        title = show.find_class('title')[0]
        link = title.cssselect('a')[0]
        show_title = link.text_content()

        if not show_title in all_shows:
            url = link.get('href')
            venue = show.find_class('venue')[0].text_content()
            genre = show.find_class('genre')[0].text_content()
            length = show.find_class('length')[0].text_content()
            length_match = re.findall(r'\d+', str(length))
            if length_match:
                length = int(length_match[0])
            else:
                length = 0

            all_shows[show_title] = {
                'url': url,
                'venue': venue,
                'genre': genre,
                'length': length,
                'showtimes': [],
            }

        all_shows[show_title]['showtimes'] += [datetime]

for (title, show) in all_shows.items():
    c.execute('INSERT INTO shows(id, name, url, venue, genre, length) VALUES(NULL, ?, ?, ?, ?, ?)',
              (title, show['url'], show['venue'], show['genre'], show['length']))
    show_id = c.lastrowid

    for time in show['showtimes']:
        parts = time.split(' ')
        day = int(parts[1][:-2])
        hour = int(parts[3].split(':')[0])
        minute = int(parts[3].split(':')[1])
        if parts[4] == 'PM' and hour != 12:
            hour += 12

        c.execute('INSERT INTO runs VALUES(?, ?, ?, ?)', (show_id, day, hour, minute))

conn.commit()

c.close()
