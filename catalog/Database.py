# database class
import json
import sqlite3

class DB:
  # create the database
  def __init__(self, db_name):
    self.db_name = db_name
    self.conn = sqlite3.connect(db_name)
    self.cur = self.conn.cursor()

  # create a new table on the database if not already exists
  def new(self, table_name, fields_list):
    fields = ', '.join(fields_list)
    self.cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({fields})")
    self.conn.commit()

  # insert one element into the database
  def insert(self, table_name, data):
    placeholders = ', '.join(['?' for _ in range(len(data))])
    self.cur.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", data)
    self.conn.commit()

  # insert a list of elements to the table
  def insert_list(self, table_name, data_list):
    for data in data_list:
      self.insert(table_name, data)
  
  # update already existing data
  def update(self, table_name, update_data):
    # example - db.update("rooms", {'condition': {'room_id': room_id}, 'new_data': {'device_id': device_id}})
    print("Updating table:", table_name)
    print("New data:", update_data['new_data'])
    
    set_clause = ', '.join([f"{field} = ?" for field in update_data['new_data'].keys()])
    condition_clause = ' AND '.join([f"{field} = ?" for field in update_data['condition'].keys()])
    condition_values = tuple(update_data['condition'].values())
    new_data_values = tuple(update_data['new_data'].values())
    query = f"UPDATE {table_name} SET {set_clause} WHERE {condition_clause}"
    
    try:
      self.cur.execute(query, new_data_values + condition_values)
      self.conn.commit()
      print("Update successful!")
    except Exception as e:
      print("Error during update:", e)
      self.conn.rollback()
  
  # search rows of a table based on conditions - returns a list of tuples
  def fetch(self, table_name, condition=None):
    if condition:
        condition_clause = ' AND '.join([f"{field} = ?" for field in condition.keys()])
        condition_values = tuple(condition.values())
        query = f"SELECT * FROM {table_name} WHERE {condition_clause}"
        self.cur.execute(query, condition_values)
    else: # all the table
        query = f"SELECT * FROM {table_name}"
        self.cur.execute(query)
    rows = self.cur.fetchall()
    return rows

  # same as fetch but returns a dictionary
  def fetch_dict(self, table_name, condition=None):
    # Construct the SQL query
    if condition:
      condition_clause = ' AND '.join([f"{field} = ?" for field in condition.keys()])
      condition_values = tuple(condition.values())
      query = f"SELECT * FROM {table_name} WHERE {condition_clause}"
      self.cur.execute(query, condition_values)
    else:
      query = f"SELECT * FROM {table_name}"
      self.cur.execute(query)
    # Fetch the rows
    rows = self.cur.fetchall()
    # Convert rows to a list of dictionaries
    result = []
    for row in rows:
      row_dict = dict(zip([column[0] for column in self.cur.description], row))
      result.append(row_dict)
    return result

  # Search for specific values in a table and retrieve the corresponding value of a specified column
  def search_first_value(self, table_name, condition, column_name):
    print(f"searching column {column_name} in {table_name}")
    # Construct the SQL query
    placeholders = ' AND '.join([f"{column} = ?" for column in condition.keys()])
    query = f"SELECT {table_name}.{column_name} FROM {table_name} WHERE {placeholders}"

    try:
      # Execute the query with the provided conditions
      self.cur.execute(query, tuple(condition.values()))
      result = self.cur.fetchone()  # Fetch the first matching row
      if result:
          return result[0]  # Return the value of the specified column
      else:
          return None  # No matching row found
    except Exception as e:
      print("Error during search:", e)
      return None
  
  # Search for specific values in a table and retrieve all the corresponding values of a specified column (list of strings)
  def search_all_values(self, table_name, condition, column_name):
    # Construct the SQL query
    placeholders = ' AND '.join([f"{column} = ?" for column in condition.keys()])
    query = f"SELECT {column_name} FROM {table_name} WHERE {placeholders}"
    try:
      # Execute the query with the provided conditions
      self.cur.execute(query, tuple(condition.values()))
      results = self.cur.fetchall()  # Fetch all matching rows
      if results:
        return [result[0] for result in results]  # Return the values of the specified column
      else:
        return []  # No matching rows found
    except Exception as e:
      print("Error during search:", e)
      return []


  # empty a table
  def reset_table(self, table_name, fields_list):
    self.cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    self.conn.commit()
    self.new(table_name, fields_list)
  
  # Delete a single line from the table based on a condition - return True if deletion was successfull, False otherwise
  def delete(self, table_name, condition):
    # Construct the SQL query
    condition_clause = ' AND '.join([f"{field} = ?" for field in condition.keys()])
    query = f"DELETE FROM {table_name} WHERE {condition_clause}"
    
    try:
      # Execute the query with the provided conditions
      self.cur.execute(query, tuple(condition.values()))
      self.conn.commit()
      return True # Returns a bool
    except Exception as e:
      print("Error during deletion:", e)
      self.conn.rollback()
      return False

  # close db - no return
  def close(self):
    self.cur.close()
    self.conn.close()

  # get table names - returns a list of strings
  def tables(self):
    # Query to retrieve table names
    self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # Fetch all table names
    tables = self.cur.fetchall()
    # Extract table names from the fetched data
    table_names = [table[0] for table in tables]
    return table_names
  
  # empty all tables, can add exceptions - no return
  def reset_database(self, exept=[]):
    tables = self.tables()
    for table_name in tables:
        if table_name not in exept:
            self.cur.execute(f"DELETE FROM {table_name}")
            self.conn.commit()
    print("All tables have been emptied except:", exept)

  # return a json with ALL the database
  def export_json_all(self):
    tables_data = {}

    # Get all table names
    self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = self.cur.fetchall()

    for table in tables:
      table_name = table[0]
      self.cur.execute(f"SELECT * FROM {table_name};")
      rows = self.cur.fetchall()
      # Convert rows to a list of dictionaries
      table_content = []
      for row in rows:
          table_content.append(dict(zip([column[0] for column in self.cur.description], row)))
      tables_data[table_name] = table_content
    return json.dumps(tables_data, indent=4)
  
  # return a json with a single table
  def export_json_table(self, table_name):
    table_data = {}
    # Check if the table exists (it should)
    if table_name not in self.tables():
      return f"Table '{table_name}' not found." 
    # Retrieve data from the specified table
    self.cur.execute(f"SELECT * FROM {table_name};")
    rows = self.cur.fetchall()
    # Convert rows to a list of dictionaries
    table_content = []
    for row in rows:
      table_content.append(dict(zip([column[0] for column in self.cur.description], row)))
    table_data[table_name] = table_content
    return json.dumps(table_data, indent=4)

  # check if a table is empty - returns bool
  def is_empty(self, table_name):
      # Query to count the number of rows in the table
      query = f"SELECT COUNT(*) FROM {table_name};"
      self.cur.execute(query)
      count = self.cur.fetchone()[0]  # Get the count of rows

      # Return True if count is 0, indicating the table is empty
      return count == 0
  
  