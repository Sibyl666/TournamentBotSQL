import sqlite3

import json


class Database:

    def __init__(self, name=None):

        self.conn = None
        self.cursor = None

        if name:
            self.open(name)
        else:
            with open('config.json') as config_file:
                data = json.load(config_file)
            self.open(data["database_file"])

    def open(self, name):

        try:
            self.conn = sqlite3.connect(name);
            self.cursor = self.conn.cursor()

        except sqlite3.Error as e:
            print("Error connecting to database!")

    def close(self):

        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self.close()

    def insert(self, table, *values):

        pragma = self.cursor.execute(f'PRAGMA table_info({table})').fetchall()
        vals = "(" + ",".join(["?" for v in pragma]) + ")"
        self.cursor.execute(f'INSERT INTO {table} VALUES {vals}', values)
        self.conn.commit()

    def select(self, table, **where):

        if where.__len__() == 0:
            self.cursor.execute(f'SELECT * FROM {table}')
        else:
            i = 1
            wstring = ""
            args = []
            for key, value in where.items():
                wstring += key + " = ?"
                args.append(value)
                if i < where.__len__():
                    wstring += " AND "
                i += 1
            self.cursor.execute(f'SELECT * FROM {table} WHERE {wstring}', args)

    def delete(self, table, **where):

        if where.__len__() == 0:
            self.cursor.execute(f'DELETE FROM {table}')
            self.conn.commit()
        else:
            i = 1
            wstring = ""
            args = []
            for key, value in where.items():
                wstring += key + " = ?"
                args.append(value)
                if i < where.__len__():
                    wstring += " AND "
                i += 1
            self.cursor.execute(f'DELETE FROM {table} WHERE {wstring}', args)
            self.conn.commit()

    def count(self, table, **where):

        if where.__len__() == 0:
            self.cursor.execute(f'SELECT COUNT(*) FROM {table}')
        else:
            i = 1
            wstring = ""
            args = []
            for key, value in where.items():
                wstring += key + " = ?"
                args.append(value)
                if i < where.__len__():
                    wstring += " AND "
                i += 1
            self.cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE {wstring}', args)
        return self.cursor.fetchone()[0]

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()
