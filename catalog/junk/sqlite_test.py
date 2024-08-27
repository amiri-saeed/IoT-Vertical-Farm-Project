import sqlite3

conn = sqlite3.connect("test_database.db")

# Create a cursor
cur = conn.cursor()

# Drop the plants table if it exists
cur.execute('''DROP TABLE IF EXISTS plants''')
conn.commit()

# Create a plants table in the database
cur.execute('''CREATE TABLE IF NOT EXISTS plants
            (plantID TEXT, plantName TEXT, typeID TEXT)''')
conn.commit()

# Example list with plant ID, plant name, and type ID
plant_list = [
    ('P1', 'Iceberg lattuce', 'L'),
    ('P2', 'Butterhead lattuce', 'L'),
    ('P3', 'Charlie', 'S'),
    ('P4', 'Barese', 'S'),
    ('P5', 'Tomato', 'T'),
    ('P6', 'Strawberry', 'T')
]

# Insert the data into the table
cur.executemany(
    '''INSERT INTO plants (plantID, plantName, typeID) VALUES(?,?,?)''', plant_list)
conn.commit()

# print to see results from db
data = cur.execute('''SELECT * FROM plants''')
for row in data:
    print(row)


# Close the cursor and connection
cur.close()
conn.close()
