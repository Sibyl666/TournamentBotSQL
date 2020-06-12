import sqlite3

import json


class Database:

    def __init__(self, name=None):

        self.conn = None
        self.cursor = None

        if name:
            self.open(name)
        else:
            self.open(self.get_config()["database_file"])

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

    @staticmethod
    def get_config():
        with open('config.json') as config_file:
            return json.load(config_file)

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

    def update(self, table, **argv):

        if argv.__len__() == 0:
            self.cursor.execute(f'UPDATE {table} SET  ')
            self.conn.commit()
        else:
            i = 1
            wstring = ""
            ustring = ""
            wargv = ""
            args = []
            for key, value in argv.items():
                if key == "where":
                    wvalues = value.split("=")
                    wstring += wvalues[0] + " = ?"
                    wargv = wvalues[1]
                    i += 1
                else:
                    ustring += key + " = ?"
                    args.append(value)
                    if i < argv.__len__():
                        ustring += ", "
                    i += 1
            args.append(wargv)
            self.cursor.execute(f'UPDATE {table} SET {ustring} WHERE {wstring}', args)
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

    def likecount(self, table, **where):

        if where.__len__() == 0:
            return self.count(table, **where)
        else:
            i = 1
            wstring = ""
            args = []
            for key, value in where.items():
                wstring += key + " LIKE ?"
                args.append(value)
                if i < where.__len__():
                    wstring += " AND "
                i += 1
            self.cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE {wstring}', args)
        return self.cursor.fetchone()[0]

    def get_next_id(self, table, group):
        self.cursor.execute(f'SELECT id FROM {table} WHERE id LIKE ? ORDER BY id DESC', (group+"_%",))
        data = self.fetchone()
        if data:
            return int(data[0].split("_")[1]) + 1
        else:
            return 1

    def commit(self):
        return self.conn.commit()

    def get_cursor(self):
        return self.cursor

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()
