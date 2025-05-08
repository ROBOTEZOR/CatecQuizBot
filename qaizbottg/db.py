import sqlite3

def init_db():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            username TEXT PRIMARY KEY,
            score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_result(username, score):
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO results (username, score) VALUES (?, ?)', (username, score))
    conn.commit()
    conn.close()
