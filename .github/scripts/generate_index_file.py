import os
import json
import sqlite3
import sys

path = sys.argv[1]


def get_json_files(prefix):
    return [f'{prefix}/{j}' for j in os.listdir(f"{path}/{prefix}")]


json_files = get_json_files('fmt') + get_json_files('x-fmt')


def insert_into_indexes(path_value: str, field_name: str, field_value: str):
    """
    Connects to the SQLite database and inserts values into the 'indexes' table.

    :param path_value: Value to insert into the 'path' column.
    :param field_name: The name
    :param field_value: Value to insert into the 'field' column.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect("/indexes")
        cursor = conn.cursor()

        # Insert values into the table
        cursor.execute("INSERT INTO indexes (path, name, field) VALUES (?, ?, ?)",
                       (path_value, field_name, field_value))

        # Commit the transaction and close the connection
        conn.commit()
        print(f"Inserted: path='{path_value}', field='{field_value}'")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()


for file_path in json_files:
    with open(f'{path}/{file_path}', 'r') as file:
        data_values = []
        data = json.load(file)
        format_name = data['formatName']
        puid = [identifier['identifierText'] for identifier in data['identifiers'] if identifier['identifierType'] == 'PUID'][0]
        for value in data.values():
            if type(value) is list:
                for each in value:
                    for obj_value in each.values():
                        if obj_value is not None:
                            data_values.append(str(obj_value))
            else:
                if value is not None:
                    data_values.append(str(value))
        field = ''.join([str(field) for field in data_values])
        insert_into_indexes(puid, format_name, field)