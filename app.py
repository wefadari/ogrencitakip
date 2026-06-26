"""
app.py - Ana Flask Uygulaması
1. Sınıf Öğrenci Takip ve Yapay Zeka Rapor Sistemi
..
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import database as db
import ai_report as ai

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'ogrenci-takip-secret-2024')

# Veritabanını başlat
db.init_db()

AVATAR_COLORS = [
    '#FF6B6B', '#FFA94D', '#FFD43B', '#69DB7C', '#4DABF7',
    '#748FFC', '#DA77F2', '#F783AC', '#4ECDC4', '#45B7D1'
]


# ==================== ANA SAYFA ====================

@app.route('/')
def index():
    """Dashboard - Ana sayfa"""
    students = db.get_all_students()
    stats = db.get_dashboard_stats()
    return render_template('index.html', students=students, stats=stats, levels=db.LEVELS)


# ==================== ÖĞRENCİ YÖNETİMİ ====================

@app.route('/ogrenciler')
def student_list():
    """Öğrenci listesi"""
    students = db.get_all_students()
    return render_template('student_list.html', students=students, levels=db.LEVELS)


@app.route('/ogrenci/ekle', methods=['GET', 'POST'])
def add_student():
    """Öğrenci ekleme"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        level = request.form.get('level', 'baslangic')
        notes = request.form.get('notes', '').strip()
        avatar_color = request.form.get('avatar_color', '#4ECDC4')

        if not name:
            flash('Öğrenci adı boş bırakılamaz!', 'error')
            return redirect(url_for('add_student'))

        student_id = db.add_student(name, level, notes, avatar_color)
        flash(f'"{name}" başarıyla eklendi! 🎉', 'success')
        return redirect(url_for('student_detail', student_id=student_id))

    return render_template('add_student.html', levels=db.LEVELS, avatar_colors=AVATAR_COLORS)


@app.route('/ogrenci/<int:student_id>')
def student_detail(student_id):
    """Öğrenci detay sayfası"""
    student = db.get_student(student_id)
    if not student:
        flash('Öğrenci bulunamadı!', 'error')
        return redirect(url_for('student_list'))

    letters = db.get_letter_tracking(student_id)
    reading_records = db.get_reading_records(student_id)
    reports = db.get_reports(student_id)

    # Grafik için veri hazırla
    chart_data = {
        'labels': [],
        'values': []
    }
    for record in reversed(reading_records[-10:]):
        date = record['recorded_at'][:10] if record['recorded_at'] else ''
        chart_data['labels'].append(date)
        chart_data['values'].append(record['words_per_minute'])

    return render_template(
        'student_detail.html',
        student=student,
        letters=letters,
        reading_records=reading_records,
        reports=reports,
        chart_data=chart_data,
        levels=db.LEVELS,
        vowels=db.VOWELS,
        consonants=db.CONSONANTS
    )


@app.route('/ogrenci/<int:student_id>/duzenle', methods=['GET', 'POST'])
def edit_student(student_id):
    """Öğrenci düzenleme"""
    student = db.get_student(student_id)
    if not student:
        flash('Öğrenci bulunamadı!', 'error')
        return redirect(url_for('student_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        level = request.form.get('level', 'baslangic')
        notes = request.form.get('notes', '').strip()
        avatar_color = request.form.get('avatar_color', '#4ECDC4')

        if not name:
            flash('Öğrenci adı boş bırakılamaz!', 'error')
            return redirect(url_for('edit_student', student_id=student_id))

        db.update_student(student_id, name, level, notes, avatar_color)
        flash(f'"{name}" bilgileri güncellendi! ✅', 'success')
        return redirect(url_for('student_detail', student_id=student_id))

    return render_template('add_student.html', student=student, levels=db.LEVELS, avatar_colors=AVATAR_COLORS)


@app.route('/ogrenci/<int:student_id>/sil', methods=['POST'])
def delete_student(student_id):
    """Öğrenci silme"""
    student = db.get_student(student_id)
    if student:
        db.delete_student(student_id)
        flash(f'"{student["name"]}" silindi.', 'info')
    return redirect(url_for('student_list'))


# ==================== HARF TAKİBİ ====================

@app.route('/ogrenci/<int:student_id>/harfler', methods=['GET', 'POST'])
def letter_tracking(student_id):
    """Harf takip sayfası"""
    student = db.get_student(student_id)
    if not student:
        flash('Öğrenci bulunamadı!', 'error')
        return redirect(url_for('student_list'))

    if request.method == 'POST':
        letter_statuses = {}
        for letter in db.TURKISH_ALPHABET:
            status = request.form.get(f'letter_{letter}', 'not_learned')
            letter_statuses[letter] = status

        db.bulk_update_letters(student_id, letter_statuses)
        flash('Harf durumları güncellendi! ✅', 'success')
        return redirect(url_for('student_detail', student_id=student_id))

    letters = db.get_letter_tracking(student_id)
    return render_template(
        'letter_tracking.html',
        student=student,
        letters=letters,
        vowels=db.VOWELS,
        consonants=db.CONSONANTS
    )


@app.route('/api/harf-guncelle', methods=['POST'])
def update_letter_api():
    """AJAX ile harf durumu güncelleme"""
    data = request.get_json()
    student_id = data.get('student_id')
    letter = data.get('letter')
    status = data.get('status')

    if not all([student_id, letter, status]):
        return jsonify({'success': False, 'error': 'Eksik parametre'}), 400

    valid_statuses = ['learned', 'partial', 'not_learned']
    if status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Geçersiz durum'}), 400

    db.update_letter_status(student_id, letter, status)

    # Güncel istatistikleri gönder
    stats = db.get_student_stats(student_id)
    return jsonify({'success': True, 'stats': stats})


# ==================== OKUMA HIZI ====================

@app.route('/ogrenci/<int:student_id>/okuma', methods=['GET', 'POST'])
def reading_speed(student_id):
    """Okuma hızı kayıt sayfası"""
    student = db.get_student(student_id)
    if not student:
        flash('Öğrenci bulunamadı!', 'error')
        return redirect(url_for('student_list'))

    if request.method == 'POST':
        try:
            wpm = int(request.form.get('words_per_minute', 0))
            if wpm <= 0:
                flash('Lütfen geçerli bir kelime sayısı girin!', 'error')
                return redirect(url_for('reading_speed', student_id=student_id))

            reading_text = request.form.get('reading_text', '').strip()
            notes = request.form.get('notes', '').strip()

            db.add_reading_record(student_id, wpm, reading_text, notes)
            flash(f'Okuma kaydı eklendi: {wpm} kelime/dakika 📖', 'success')
            return redirect(url_for('student_detail', student_id=student_id))

        except ValueError:
            flash('Lütfen sayısal bir değer girin!', 'error')

    records = db.get_reading_records(student_id)
    return render_template('reading_speed.html', student=student, records=records)


@app.route('/okuma-sil/<int:record_id>', methods=['POST'])
def delete_reading_record(record_id):
    """Okuma kaydını sil"""
    student_id = request.form.get('student_id')
    db.delete_reading_record(record_id)
    flash('Okuma kaydı silindi.', 'info')
    return redirect(url_for('student_detail', student_id=student_id))


# ==================== AI RAPOR ====================

@app.route('/ogrenci/<int:student_id>/rapor-olustur', methods=['POST'])
def generate_report(student_id):
    """AI raporu oluştur ve kaydet"""
    student = db.get_student(student_id)
    if not student:
        flash('Öğrenci bulunamadı!', 'error')
        return redirect(url_for('student_list'))

    letters = db.get_letter_tracking(student_id)
    reading_records = db.get_reading_records(student_id)

    try:
        report_text = ai.generate_report(student, letters, reading_records)
        report_id = db.save_report(student_id, report_text)
        flash('Yapay zeka raporu başarıyla oluşturuldu! 🤖✨', 'success')
        return redirect(url_for('view_report', report_id=report_id))
    except Exception as e:
        flash(f'Rapor oluşturulurken hata: {str(e)}', 'error')
        return redirect(url_for('student_detail', student_id=student_id))


@app.route('/rapor/<int:report_id>')
def view_report(report_id):
    """Rapor görüntüleme"""
    report = db.get_report(report_id)
    if not report:
        flash('Rapor bulunamadı!', 'error')
        return redirect(url_for('index'))

    student = db.get_student(report['student_id'])
    return render_template('report.html', report=report, student=student)


@app.route('/rapor/<int:report_id>/sil', methods=['POST'])
def delete_report(report_id):
    """Raporu sil"""
    report = db.get_report(report_id)
    student_id = report['student_id'] if report else None

    conn = db.get_db()
    conn.execute('DELETE FROM ai_reports WHERE id=?', (report_id,))
    conn.commit()
    conn.close()

    flash('Rapor silindi.', 'info')
    if student_id:
        return redirect(url_for('student_detail', student_id=student_id))
    return redirect(url_for('index'))


# ==================== API ====================

@app.route('/api/ogrenci-istatistik/<int:student_id>')
def student_stats_api(student_id):
    """Öğrenci istatistikleri API"""
    stats = db.get_student_stats(student_id)
    return jsonify(stats)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 50)
    print("EduTrack - 1. Sinif Ogrenci Takip Sistemi")
    print("http://localhost:5000 adresinden erisebilirsiniz")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
