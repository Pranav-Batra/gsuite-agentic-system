import psycopg

# Connect to an existing database
with psycopg.connect('port=5432 dbname=test user=postgres password=Cheeseisfun@1') as conn:

    # Open a cursor to perform database operations
    with conn.cursor() as cur:

        # Execute a command: this creates a new table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE,
                refresh_token TEXT UNIQUE,
                sql_bucket_path TEXT UNIQUE)
            """)

        # Pass data to fill a query placeholders and let Psycopg perform
        # the correct conversion (no SQL injections!)
        cur.execute(
            "INSERT INTO users (email, refresh_token, sql_bucket_path) VALUES (%s, %s, %s)",
            ('test@mail.com', "random-refresh", "fake_path"))

        # Query the database and obtain data as Python objects.
        cur.execute("SELECT * FROM users")
        print(cur.fetchone())

        # You can use `cur.executemany()` to perform an operation in batch
        # cur.executemany(
        # #     "INSERT INTO test (num) values (%s)",
        # #     [(33,), (66,), (99,)])

        # # # You can use `cur.fetchmany()`, `cur.fetchall()` to return a list
        # # # of several records, or even iterate on the cursor
        # # cur.execute("SELECT id, num FROM test order by num")
        # # for record in cur:
        # #     print(record)

        # Make the changes to the database persistent
        conn.commit()
