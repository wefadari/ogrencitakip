"""
database.py - Veritabanı işlemleri
SQLite kullanarak öğrenci verilerini yönetir.
"""
import os
import psycopg2

def get_db():
    # Vercel'e eklediğimiz DATABASE_URL değişkenini kullanıyoruz
    db_url = os.environ.get('DATABASE_URL')
    # Neon/PostgreSQL kullanıyorsanız psycopg2 ile bağlantı
    conn = psycopg2.connect(db_url)
    return conn
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'students.db')

TURKISH_ALPHABET = [
    'A', 'B', 'C', 'Ç', 'D', 'E', 'F', 'G', 'Ğ',
    'H', 'I', 'İ', 'J', 'K', 'L', 'M', 'N', 'O',
    'Ö', 'P', 'R', 'S', 'Ş', 'T', 'U', 'Ü', 'V', 'Y', 'Z'
]

VOWELS = ['A', 'E', 'I', 'İ', 'O', 'Ö', 'U', 'Ü']
CONSONANTS = [l for l in TURKISH_ALPHABET if l not in VOWELS]

LEVELS = {
    'baslangic': {'label': 'Başlangıç', 'color': '#FF6B6B', 'icon': '🌱'},
    'gelisiyor': {'label': 'Gelişiyor', 'color': '#FFA94D', 'icon': '🌿'},
    'orta': {'label': 'Orta Düzey', 'color': '#FFD43B', 'icon': '🌻'},
    'iyi': {'label': 'İyi', 'color': '#51CF66', 'icon': '⭐'},
    'mukemmel': {'label': 'Mükemmel', 'color': '#339AF0', 'icon': '🏆'},
}


def get_db():
    """Veritabanı bağlantısı döndürür."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Veritabanı tablolarını oluşturur."""
    conn = get_db()
    cursor = conn.cursor()

    # Öğrenciler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT DEFAULT 'baslangic',
            notes TEXT DEFAULT '',
            avatar_color TEXT DEFAULT '#4ECDC4',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Harf takibi tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS letter_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            letter TEXT NOT NULL,
            status TEXT DEFAULT 'not_learned',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, letter)
        )
    ''')

    # Okuma hızı tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            words_per_minute INTEGER NOT NULL,
            reading_text TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    ''')

    # AI raporlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            report_text TEXT NOT NULL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


# ===== ÖĞRENCİ İŞLEMLERİ =====

def add_student(name, level='baslangic', notes='', avatar_color='#4ECDC4'):
    """Yeni öğrenci ekler."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO students (name, level, notes, avatar_color) VALUES (?, ?, ?, ?)',
        (name, level, notes, avatar_color)
    )
    student_id = cursor.lastrowid

    # Tüm harfleri "öğrenilmedi" olarak başlat
    for letter in TURKISH_ALPHABET:
        cursor.execute(
            'INSERT INTO letter_tracking (student_id, letter, status) VALUES (?, ?, ?)',
            (student_id, letter, 'not_learned')
        )

    conn.commit()
    conn.close()
    return student_id


def get_all_students():
    """Tüm öğrencileri listeler."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students ORDER BY name')
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Her öğrenci için istatistik ekle
    for student in students:
        stats = get_student_stats(student['id'])
        student.update(stats)
        student['level_info'] = LEVELS.get(student['level'], LEVELS['baslangic'])

    return students


def get_student(student_id):
    """Belirli bir öğrencinin bilgilerini getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    student = dict(row)
    student['level_info'] = LEVELS.get(student['level'], LEVELS['baslangic'])
    student['stats'] = get_student_stats(student_id)
    return student


def update_student(student_id, name, level, notes, avatar_color):
    """Öğrenci bilgilerini günceller."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE students SET name=?, level=?, notes=?, avatar_color=? WHERE id=?',
        (name, level, notes, avatar_color, student_id)
    )
    conn.commit()
    conn.close()


def delete_student(student_id):
    """Öğrenciyi siler."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()


def get_student_stats(student_id):
    """Öğrenci istatistiklerini hesaplar."""
    conn = get_db()
    cursor = conn.cursor()

    # Harf istatistikleri
    cursor.execute(
        "SELECT status, COUNT(*) as count FROM letter_tracking WHERE student_id=? GROUP BY status",
        (student_id,)
    )
    letter_stats = {row['status']: row['count'] for row in cursor.fetchall()}

    learned = letter_stats.get('learned', 0)
    partial = letter_stats.get('partial', 0)
    not_learned = letter_stats.get('not_learned', 0)
    total = len(TURKISH_ALPHABET)
    progress = round((learned + partial * 0.5) / total * 100)

    # Son okuma hızı
    cursor.execute(
        'SELECT words_per_minute FROM reading_records WHERE student_id=? ORDER BY recorded_at DESC LIMIT 1',
        (student_id,)
    )
    row = cursor.fetchone()
    last_wpm = row['words_per_minute'] if row else 0

    conn.close()

    return {
        'letters_learned': learned,
        'letters_partial': partial,
        'letters_not_learned': not_learned,
        'letter_progress': progress,
        'last_wpm': last_wpm,
    }


# ===== HARF TAKİBİ =====

def get_letter_tracking(student_id):
    """Öğrencinin harf durumlarını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT letter, status FROM letter_tracking WHERE student_id=? ORDER BY letter',
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Alfabetik sırayla döndür
    letter_map = {row['letter']: row['status'] for row in rows}
    result = []
    for letter in TURKISH_ALPHABET:
        result.append({
            'letter': letter,
            'status': letter_map.get(letter, 'not_learned'),
            'is_vowel': letter in VOWELS
        })
    return result


def update_letter_status(student_id, letter, status):
    """Harf durumunu günceller."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO letter_tracking (student_id, letter, status, updated_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(student_id, letter) DO UPDATE SET status=?, updated_at=CURRENT_TIMESTAMP''',
        (student_id, letter, status, status)
    )
    conn.commit()
    conn.close()


def bulk_update_letters(student_id, letter_statuses):
    """Birden fazla harfi aynı anda günceller."""
    conn = get_db()
    cursor = conn.cursor()
    for letter, status in letter_statuses.items():
        cursor.execute(
            '''INSERT INTO letter_tracking (student_id, letter, status, updated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(student_id, letter) DO UPDATE SET status=?, updated_at=CURRENT_TIMESTAMP''',
            (student_id, letter, status, status)
        )
    conn.commit()
    conn.close()


# ===== OKUMA HIZI =====

def add_reading_record(student_id, words_per_minute, reading_text='', notes=''):
    """Okuma hızı kaydı ekler."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reading_records (student_id, words_per_minute, reading_text, notes) VALUES (?, ?, ?, ?)',
        (student_id, words_per_minute, reading_text, notes)
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_reading_records(student_id):
    """Öğrencinin okuma hızı kayıtlarını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM reading_records WHERE student_id=? ORDER BY recorded_at DESC',
        (student_id,)
    )
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def delete_reading_record(record_id):
    """Okuma kaydını siler."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reading_records WHERE id=?', (record_id,))
    conn.commit()
    conn.close()


# ===== AI RAPORLAR =====

def save_report(student_id, report_text):
    """AI raporunu kaydeder."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO ai_reports (student_id, report_text) VALUES (?, ?)',
        (student_id, report_text)
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_reports(student_id):
    """Öğrencinin tüm raporlarını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM ai_reports WHERE student_id=? ORDER BY generated_at DESC',
        (student_id,)
    )
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports


def get_report(report_id):
    """Belirli bir raporu getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ai_reports WHERE id=?', (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ===== GENEL İSTATİSTİKLER =====

def get_dashboard_stats():
    """Dashboard için genel istatistikler."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM students')
    total_students = cursor.fetchone()['total']

    cursor.execute(
        "SELECT COUNT(*) as count FROM students WHERE level IN ('iyi', 'mukemmel')"
    )
    advanced_students = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM reading_records')
    total_readings = cursor.fetchone()['count']

    cursor.execute('SELECT AVG(words_per_minute) as avg FROM reading_records')
    row = cursor.fetchone()
    avg_wpm = round(row['avg']) if row['avg'] else 0

    conn.close()

    return {
        'total_students': total_students,
        'advanced_students': advanced_students,
        'total_readings': total_readings,
        'avg_wpm': avg_wpm,
    }
