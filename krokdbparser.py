#!/usr/bin/env python
from __future__ import print_function

import sqlite3
import re

krokquote_files = ['krok_02052016.txt', 'krok_02082016.txt', 'krok_02092016.txt', 'krok_02102016.txt', 'krok_02112016.txt', 'krok_02122016.txt', 'krok_02142016.txt', 'krok_02152016.txt', 'krok_02232016.txt', 'krok_162016.txt']

for k_file in krokquote_files:
    conn = sqlite3.connect('krokquotes.db')
    c = conn.cursor()

    krokquotefile = open(k_file, 'r')

    for line in krokquotefile:
        line2 = line.replace('"', '')
        if not re.match(r'^lol|yeah|enmand|mike|microburn|Syini666|TheHorse13|dave|e-mod|kike-mod|orcam|back|DrCheese|cobalt|sure|idk|what|whoa|NOW|30|Cto|Hmm|LOL|no|,|I am|Haha|haha|s6[work]|s6[home]', line2):
            print (line2, end="")
            c.execute('''INSERT INTO bestkrok(quote) VALUES (:quote)''', {'quote':line2})

    conn.commit()
    conn.close()
    krokquotefile.close()
