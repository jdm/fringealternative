from lxml.html import parse
import sqlite3
import re

conn = sqlite3.connect('shows.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS shows')
c.execute('DROP TABLE IF EXISTS runs')
c.execute('CREATE TABLE shows (id integer PRIMARY KEY, name text, url text, venue text, genre text, length integer)')
c.execute('CREATE TABLE runs (show_id integer, day integer, hour integer, minute integer, FOREIGN KEY(show_id) REFERENCES shows(id))')

tree = parse('full.html').getroot()
shows = tree.find_class('show')
for show in shows:
    link = show.cssselect('a')[0]
    url = link.get('href')
    title = link.text_content()
    venue = show.find_class('venue')[0].text_content()
    genre = show.find_class('genre')[0].text_content()
    length = show.find_class('length')[0].text_content()
    length_match = re.findall(r'\d+', str(length))
    if length_match:
        length = int(length_match[0])
    else:
        length = 0
    times = show.find_class('showtimes')
    if not times:
        continue

    c.execute('INSERT INTO shows(id, name, url, venue, genre, length) VALUES(NULL, ?, ?, ?, ?, ?)',
              (title, url, venue, genre, length))

    show_id = c.lastrowid

    times[0][0].drop_tree() # get rid of the <strong>Show times</strong>
    alltimes = times[0].text_content()
    for time in alltimes.split(','):
        data = time.split()
        day = int(data[1])
        hour = int(data[2].split(':')[0])
        minute = int(data[2].split(':')[1])
        if data[3] == 'PM' and hour != 12:
            hour += 12
        c.execute('INSERT INTO runs VALUES(?, ?, ?, ?)', (show_id, day, hour, minute))

conn.commit()
    
c.close()
