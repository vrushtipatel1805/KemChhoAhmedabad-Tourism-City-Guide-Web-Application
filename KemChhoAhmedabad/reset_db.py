import os
import time

db_file = 'kemchho.db'
if os.path.exists(db_file):
    try:
        os.remove(db_file)
        print(f"Deleted {db_file}")
    except PermissionError:
        print(f"Cannot delete {db_file}, it might be in use.")
else:
    print(f"{db_file} not found")
