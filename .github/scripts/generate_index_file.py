import json
import os
import sqlite3
import sys
import uuid

path = sys.argv[1]


def get_json_files(prefix):
    return [f"{prefix}/{j}" for j in os.listdir(f"{path}/signatures/{prefix}")]


json_files = get_json_files("fmt") + get_json_files("x-fmt")


def create_table():
    conn = sqlite3.connect("indexes")
    try:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS formats")
        cursor.execute("DROP TABLE IF EXISTS extensions")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS formats (id, path, name, field)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS extensions (name, format_id)"
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


def insert_into_database(
    path_value: str, field_name: str, extension_names: str, field_value: str
):
    conn = sqlite3.connect("indexes")
    try:
        format_id = str(uuid.uuid4())
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO formats (id, path, name, field) VALUES (?, ?, ?, ?)",
            (format_id, path_value, field_name, field_value),
        )
        for extension_name in extension_names:
            cursor.execute(
                "INSERT INTO extensions (name, format_id) VALUES (?, ?)",
                (extension_name, format_id),
            )
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


def run():
    create_table()
    for file_path in json_files:

        with open(f"{path}/signatures/{file_path}", "r") as file:
            data = json.load(file)
            version = (
                " " + data["version"] if "version" in data and data["version"] else ""
            )
            format_name = data["formatName"] + version
            puid = [
                idf["identifierText"]
                for idf in data["identifiers"]
                if idf["identifierType"] == "PUID"
            ][0]
            external_signatures = (
                data["externalSignatures"] if "externalSignatures" in data else []
            )
            file_extension_list = [
                x for x in external_signatures if x["signatureType"] == "File extension"
            ]
            extension_names = [fe["externalSignature"] for fe in file_extension_list]
            file_extension = "".join(extension_names)
            field = "".join([format_name, file_extension])
            insert_into_database(puid, format_name, extension_names, field)


run()
