# create, fill and then empty a table

from database import DB

if __name__ == "__main__":
    db = DB("test_database.db")
    db.new("plants", ["plantID TEXT", "plantName TEXT", "typeID TEXT"])
    
    plant_list = [
        ('P1', 'Iceberg lattuce', 'L'),
        ('P2', 'Butterhead lattuce', 'L'),
        ('P3', 'Charlie', 'S'),
        ('P4', 'Barese', 'S'),
        ('P5', 'Tomato', 'T'),
        ('P6', 'Strawberry', 'T')
    ]
    
    for plant in plant_list:
        db.insert("plants", plant)

    print("Original data:")
    print(db.fetch_all("plants"))

    # Update the data
    db.update("plants", {"plantName": "New Name"}, {"plantID": "P1"})

    print("\nData after update:")
    print(db.fetch_all("plants"))
    
    # Reset the table with the same fields list
    db.reset_table("plants", ["plantID TEXT", "plantName TEXT", "typeID TEXT"])

    print("\nTable reset:")
    print(db.fetch_all("plants"))

    db.close()
