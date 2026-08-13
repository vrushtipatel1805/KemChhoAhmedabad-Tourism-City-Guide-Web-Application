import sqlite3

conn = sqlite3.connect('kemchho.db')
cursor = conn.cursor()

print("Deleting photographer with ID 2 (Harsiddh shah)...")
cursor.execute("DELETE FROM photographers WHERE id = 2")
conn.commit()

print("Deletion complete. verifying...")
cursor.execute("SELECT id, username FROM photographers")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
