import logging

import pandas as pd
import psycopg2
import psycopg2.extras as extras
from backend.utils import setup_logging


class SQL:
    def __init__(self, **kwargs):
        self.logger = None
        setup_logging(self, logging.INFO)

        host = kwargs.get("host")
        database = kwargs.get("database")
        user = kwargs.get("user")
        password = kwargs.get("password")

        self.conn = psycopg2.connect(
            host=host, database=database, user=user, password=password
        )

        self.conn.autocommit = True

    def df2sql_table(self, df, table_name):
        cursor = self.conn.cursor()
        df.to_sql(table_name, self.conn, if_exists="append", index=False)

        query = f"SELECT * from {table_name}"
        cursor.execute(query)
        for i in cursor.fetchall():
            self.logger.info(i)

        return self.conn.commit()

    def sql_table2df(self, table_name, cols, add_query=""):
        query = f"SELECT * FROM {table_name}"
        query += add_query
        query_handle = pd.read_sql_query(query, self.conn)
        df = pd.DataFrame(query_handle, columns=cols)
        return df

    def execute_values(self, df, table):
        tuples = [tuple(x) for x in df.to_numpy()]
        cols = ",".join(list(df.columns))

        self.logger.debug(cols)
        # SQL query to execute
        query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
        self.logger.debug(query)
        cursor = self.conn.cursor()
        try:
            extras.execute_values(cursor, query, tuples)
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return 1
        self.logger.info("the dataframe is inserted")
        cursor.close()
        return

    def get_subreddits(
        self,
    ):
        query = "SELECT DISTINCT subreddit_display_name FROM submissions;"
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.conn.commit()

            # parse retrieved results
            parsed_result = list()
            for r in result:
                _id = r[0]
                parsed_result.append(_id)
            cursor.close()
            return parsed_result
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return list()

    # http://www.silota.com/docs/recipes/sql-top-n-group.html

    def get_submissions(self, subreddit_name: str) -> list:
        query = f"""
        SELECT 
            *
        FROM
            submissions
        INNER JOIN 
            submissions_user_engagement
        ON 
            submissions_user_engagement.submission_id = submissions.submission_id
        WHERE
            submissions.subreddit_display_name = '{subreddit_name}'
        ORDER BY
            user_engagement DESC;
        """

        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.conn.commit()

            # parse retrieved results
            parsed_result = list()
            for r in result:
                parsed_result.append(r)
            cursor.close()
            return parsed_result
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return list()

    def get_comments(self, submission_id: str):
        query = (
            f"SELECT * FROM reddit_comments WHERE submission_id = '{submission_id}';"
        )
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.conn.commit()

            # parse retrieved results
            parsed_result = list()
            for r in result:
                parsed_result.append(r)
            cursor.close()
            return parsed_result
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return list()

        return

    def get_column_from_table(self, table, column_name, add_query=""):
        query = f"SELECT {column_name} from {table}"
        query += add_query

        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.conn.commit()

            # parse retrieved results
            parsed_result = list()
            for r in result:
                _id = r[0]
                parsed_result.append(_id)
            cursor.close()
            return parsed_result

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return list()

    def get_topn_submissions(self, top_nth: int, interval: str):
        if top_nth <= 0:
            return

        query = f"""
        SELECT *
        FROM (
            SELECT 
                *, ROW_NUMBER() OVER (PARTITION BY submissions.subreddit_id ORDER BY user_engagement DESC) AS ua_rank
            FROM
                submissions
            INNER JOIN 
                submissions_user_engagement
            ON 
                submissions_user_engagement.submission_id = submissions.submission_id
            WHERE created > now() - interval '{interval}'
            ORDER BY
		        user_engagement DESC
        ) ranks
        WHERE ua_rank <= {top_nth}
        
        """

        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.conn.commit()

            # parse retrieved results
            parsed_result = list()
            for r in result:
                parsed_result.append(r)
            cursor.close()
            return parsed_result
        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.info("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return list()
        return

    def close_conn(
        self,
    ):
        self.conn.close()
