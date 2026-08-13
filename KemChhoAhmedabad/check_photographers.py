import sqlite3

conn = sqlite3.connect('kemchho.db')
cursor = conn.cursor()

print("Checking photographers table:")
cursor.execute("SELECT id, username FROM photographers")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
