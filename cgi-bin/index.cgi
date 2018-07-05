#!/usr/bin/env python2

# enable debugging
import cgitb
import cgi
cgitb.enable()

print "Content-Type: text/html;charset=utf-8"
print

import sqlite3
import time
from datetime import datetime, timedelta, date, tzinfo, timedelta

class EST(tzinfo):
    def utcoffset(self, dt):
      return timedelta(hours=-4)

    def dst(self, dt):
        return timedelta(0)

today = datetime.now(EST())

form = cgi.FieldStorage()
cur_month = int(form.getfirst('cur_month', str(today.month)))
cur_day = int(form.getfirst('cur_day', str(today.day)))
cur_hour = int(form.getfirst('cur_hour', str(today.hour)))
cur_min = int(form.getfirst('cur_min', str(today.minute)))

conn = sqlite3.connect('shows.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('select * from venues')
venues = {}
for row in c.fetchall():
    venues[row['id']] = { 'name': row['name'], 'address': row['address'] }

c.execute('select * from shows, runs where runs.show_id = shows.id and runs.day = ? and (runs.hour > ? or (runs.hour = ? and runs.minute >= ?)) order by runs.hour, runs.minute, shows.length asc', (cur_day, cur_hour, cur_hour, cur_min))

def min_format(min):
    if min < 10:
        return '0' + str(min)
    return str(min)

print '<!DOCTYPE html>'
print '<html><head><style>th { text-align: left; }</style><title>Fringe Showtime Listing</title></head><body>'
print '<center><h2>Fringe Showtime Listing</h2>'
print '<span>by <a href="http://www.joshmatthews.net">Josh Matthews</a> (<a href="http://www.github.com/jdm/fringealternative/">source</a>; patches accepted!)</span></center><br>'
print '<form action="index.cgi" method="post"><div>'
print 'Show schedule for: <select name="cur_month">'
print '<option value="6"%s>June</option>' % (' selected' if 6 == cur_month else '')
print '<option value="7"%s>July</option>' % (' selected' if 7 == cur_month else '')
print '</select>'
print '<select name="cur_day">'
for day in xrange(1, 31):
    print '<option value="%s"%s>%s</option>' % (day, ' selected' if day == cur_day else '', day)
print '</select>, 2016, starting from '
print '<select name="cur_hour">'
for hour in xrange(0, 25):
    print '<option value="%s"%s>%s</option>' % (hour, ' selected' if hour == cur_hour else '', hour)
print '</select>'
print ':'
print '<select name="cur_min">'
for min in xrange(0, 61):
    print '<option value="%s"%s>%s</option>' % (min, ' selected' if min == cur_min else '', min_format(min))
print '</select>'

print '</div><input type="submit" value="Submit"></form><br><br>'

print '<table cellspacing=10px>'
print '<th>Title</th><th>Venue</th><th>End time</th>'
last_time = None
for row in c.fetchall():
    time = str(row['hour']) + ':' + min_format(row['minute'])
    if not last_time or last_time != time:
        last_time = time
        print '<tr><td colspan=2><h5>', time, '</h5></td></tr>'

    end_time = timedelta(minutes=row['length']) + datetime(year=2016, month=cur_month, day=cur_day, hour=row['hour'], minute=row['minute'])

    print '<tr>'
    print '<td><a href="%s">%s</a></td><td><a href="%s">%s</a></td><td>%s</td>' % (
        row['url'],
        row['name'].encode('ascii', 'ignore'),
        'https://www.google.ca/maps/place/' + venues[row['venue_id']]['address'].replace(' ', '+'),
        venues[row['venue_id']]['name'],
        str(end_time.hour) + ':' + min_format(end_time.minute)
    )
    print '</tr>'

print '</table>'
print '</body></html>'

c.close()
