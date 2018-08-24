import sys
import os
import urllib.parse
import psycopg2


class Query_Executor:
    """
    Small helper class to execute query, and log them if there is an error
    """
    def __init__(self, parameters):
        self.log_file = os.path.join(parameters['paths']['program_path'], parameters['paths']['sql_error_log'])

        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

        self.connection = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        self.connection.autocommit = True
        # I think postgres defaults to the right character encoding already
        # charset='utf8mb4',


    def execute(self, sql_command):
        connection = self.connection
        cursor = connection.cursor()
        try:
            #~ cursor.execute('SET ROLE pubmed_role;')
            cursor.execute(sql_command)
            connection.close()

        except:
            exception = sys.exc_info()[1]
            errors_log = open(self.log_file, 'a')
            errors_log.write('{} - {}\n'.format(exception, sql_command))
            errors_log.close()
            print('{} - {}\n'.format(exception, sql_command))
