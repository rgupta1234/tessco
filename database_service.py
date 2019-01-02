import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseService:
    def __init__(self, host, username, password, db_name, schema, port):
        self.db_host = host
        self.db_username = username
        self.db_password = password
        self.db_name = db_name
        self.db_schema = schema
        self.db_port = port
        self.connection = None

    def __del__(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None

    def select_first_row(self, sql, parameters):
        cursor = self.get_cursor()
        cursor.execute(sql.format(self.db_schema), parameters)
        result = cursor.fetchone()
        cursor.close()
        return result

    def select_all_rows(self, sql, parameters):
        cursor = self.get_cursor()
        cursor.execute(sql.format(self.db_schema), parameters)
        result = cursor.fetchall()
        cursor.close()
        return result

    def execute_cmd(self, sql, parameters):
        with self.get_cursor() as cursor:
            cursor.execute(sql.format(self.db_schema), parameters)
            self.connection.commit()

    def get_cursor(self):
        if not self.connection:
            self.connection = psycopg2.connect(host=self.db_host, user=self.db_username, password=self.db_password,
                                               dbname=self.db_name, port=self.db_port)
        return self.connection.cursor(cursor_factory=RealDictCursor)
