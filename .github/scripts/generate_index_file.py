import os
import json
import sqlite3
import sys

path = sys.argv[1]


def get_json_files(prefix):
    return [f'{prefix}/{j}' for j in os.listdir(f"{path}/signatures/{prefix}")]


json_files = get_json_files('fmt') + get_json_files('x-fmt')


def create_table():
    conn = sqlite3.connect("indexes")
    try:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS indexes")
        cursor.execute("CREATE TABLE IF NOT EXISTS indexes (path, name, field)")
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


def insert_into_indexes(path_value: str, field_name: str, field_value: str):
    conn = sqlite3.connect("indexes")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO indexes (path, name, field) VALUES (?, ?, ?)",
                       (path_value, field_name, field_value))

        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


def run():
    create_table()
    for file_path in json_files:

        with open(f'{path}/signatures/{file_path}', 'r') as file:
            data_values = []
            data = json.load(file)
            format_name = data['formatName']
            puid = [idf['identifierText'] for idf in data['identifiers'] if idf['identifierType'] == 'PUID'][0]
            external_signatures = data['externalSignatures'] if 'externalSignatures' in data else []
            file_extension_list = [x for x in external_signatures if x['signatureType'] == 'File Extension']
            file_extension = file_extension_list[0] if len(file_extension_list) > 1 else ''
            field = ''.join([format_name, file_extension])
            insert_into_indexes(puid, format_name, field)


run()
