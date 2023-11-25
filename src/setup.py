from pathlib import Path
import re
import sqlite3


def create_strips_table(cursor: sqlite3.Cursor):
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS strips (id INTEGER PRIMARY KEY AUTOINCREMENT, number INTEGER, title TEXT, url TEXT, newspost TEXT)"
    )

    with open("scraper/data/titles.txt") as txt:
        num_titles = [line.split() for line in txt]

    numbers = [int(line[0]) for line in num_titles]
    titles = [line[1] for line in num_titles]
    urls = [f"https://www.questionablecontent.net/view.php?comic={i}" for i in numbers]
    fold = Path("scraper/data/newsposts")
    newsposts = [(fold / f"{i}.txt").read_text() for i in numbers]

    cursor.executemany(
        "INSERT INTO strips (number, title, url, newspost) VALUES (?,?,?,?)",
        zip(numbers, titles, urls, newsposts),
    )

    for row in cursor:
        print(row)

    response = input("Commit create_strips_table? (y/[N]):")
    if response == "y" or response == "Y" or response == "yes" or response == "Yes":
        cursor.connection.commit()


def update_strips_table(cursor: sqlite3.Cursor):
    cursor.execute("SELECT id, url FROM strips")
    ids = list()
    old_urls = list()
    for row in cursor:
        ids.append(row[0])
        old_urls.append(row[1])

    new_urls = list()
    for url in old_urls:
        new_urls.append(re.sub(r"(https:.*)\.com(/view.*)", r"\1.net\2", url))

    print(new_urls)

    cursor.executemany("UPDATE strips SET url =? WHERE id =?", zip(new_urls, ids))

    for row in cursor:
        print(row)

    response = input("Commit create_strips_table? (y/[N]):")
    if response == "y" or response == "Y" or response == "yes" or response == "Yes":
        cursor.connection.commit()


def setup_characters_table(cursor: sqlite3.Cursor):
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, url TEXT)"
    )
    character_file = Path("scraper/data/characters.txt")
    lines = character_file.read_text().splitlines()
    names = [" ".join(line.split()[:-1]) for line in lines]
    urls = [line.split()[-1] for line in lines]

    cursor.executemany(
        "INSERT INTO characters (name, url) VALUES (?,?)", zip(names, urls)
    )

    for row in cursor:
        print(row)

    response = input("Commit create_strips_table? (y/[N]):")
    if response == "y" or response == "Y" or response == "yes" or response == "Yes":
        cursor.connection.commit()


def main():
    with sqlite3.connect("db/questionable_content.db") as db:
        cursor = db.cursor()
        for row in cursor.execute("SELECT * FROM characters"):
            print(row)
        # update_strips_table(cursor)
        # create_strips_table(cursor)
        # setup_characters_table(cursor)


if __name__ == "__main__":
    main()
