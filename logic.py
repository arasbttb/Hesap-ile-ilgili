import sqlite3
from datetime import datetime
from config import DATABASE 
import os
import cv2

class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
            )
        ''')

            conn.commit()

    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('INSERT INTO users VALUES (?, ?)', (user_id, user_name))
            conn.commit()

    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany('''INSERT INTO prizes (image) VALUES (?)''', data)
            conn.commit()

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
            if cur.fetchall():
                return 0
            else:
                conn.execute('''INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)''', (user_id, prize_id, win_time))
                conn.commit()
                return 1

    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)  # Bu satır eksikti!
        with conn:
            conn.execute('''UPDATE prizes SET used = 1 WHERE prize_id = ?''', (prize_id,))
            conn.commit()

    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users')
            result = cur.fetchall()
            return [x[0] for x in result] if result else []
        # Gereksiz return satırı kaldırıldı

    def get_random_prize(self):  # Sadece bir tane kaldı
        try:
            conn = sqlite3.connect(self.database)
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM prizes WHERE used = 0 ORDER BY RANDOM() LIMIT 1")
                result = cur.fetchall()
                return result[0] if result else None
        except Exception as e:
            print(f"Hata: {e}")
            return None

def hide_img(img_name):
    try:
        # Klasör yoksa oluştur
        os.makedirs('hidden_img', exist_ok=True)
        
        image = cv2.imread(f'img/{img_name}')
        if image is None:
            print(f"Resim bulunamadı: {img_name}")
            return
            
        blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
        pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
        pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)
        print(f"Gizli resim oluşturuldu: {img_name}")
    except Exception as e:
        print(f"Resim işlenirken hata: {e}")

if __name__ == '__main__':
    try:
        manager = DatabaseManager(DATABASE)
        manager.create_tables()
        
        # img klasörü var mı kontrol et
        if os.path.exists('img'):
            prizes_img = os.listdir('img')
            if prizes_img:
                data = [(x,) for x in prizes_img]
                manager.add_prize(data)
                print(f"{len(prizes_img)} ödül eklendi")
                
                # Her resim için gizli versiyon oluştur
                for img in prizes_img:
                    hide_img(img)
            else:
                print("img klasöründe resim yok")
        else:
            print("img klasörü bulunamadı")
            
    except Exception as e:
        print(f"Program hatası: {e}")