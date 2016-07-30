#!/usr/bin/env python

import sqlite3
from random import randint

conn = sqlite3.connect('krokquotes.db')
items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote != '';")
i = 0
for item in items:
	i += 1
rnd = randint(0,i)
items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote != '';")
for q in items:
	if q[0] == rnd:
		print q[1]
