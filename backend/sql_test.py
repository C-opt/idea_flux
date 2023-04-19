from miner import SQL


def main():

    sql_handle = SQL(
        host="localhost",
        database="ideaflux",
        user="postgres",
        password="postgres",
    )
    cols = ["comment_id", "parent_id", "submission_id", "body"]
    df = sql_handle.sql_table2df("reddit_comments", cols)
    print(df)
    return


main()
