
import sqlite3

connection = sqlite3.connect("reminders.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM server_settings")

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()
