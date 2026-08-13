import sqlite3

def set_admin(email):
    conn = sqlite3.connect('kemchho.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
    if cursor.rowcount > 0:
        print(f"User {email} is now an admin.")
    else:
        print(f"User {email} not found.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    email = input("Enter email to make admin: ")
    set_admin(email)
