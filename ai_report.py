"""
ai_report.py - Yapay Zeka Rapor Üretimi
Google Gemini API kullanarak Türkçe öğrenci raporu oluşturur.
"""

import os
try:
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_SDK = False
from database import LEVELS, TURKISH_ALPHABET


def configure_ai():
    """Gemini AI'ı yapılandırır."""
    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key or api_key == 'buraya_api_anahtarinizi_girin':
        return None
    if USE_NEW_SDK:
        client = genai.Client(api_key=api_key)
        return client
    else:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')


def generate_report(student, letter_tracking, reading_records):
    """
    Öğrenci verilerini analiz ederek Türkçe rapor üretir.
    
    Args:
        student: Öğrenci bilgileri dict
        letter_tracking: Harf takip listesi
        reading_records: Okuma kayıtları listesi
    
    Returns:
        str: Oluşturulan rapor metni
    """
    model = configure_ai()

    # Veri analizi
    learned = [lt['letter'] for lt in letter_tracking if lt['status'] == 'learned']
    partial = [lt['letter'] for lt in letter_tracking if lt['status'] == 'partial']
    not_learned = [lt['letter'] for lt in letter_tracking if lt['status'] == 'not_learned']

    # Okuma istatistikleri
    wpm_list = [r['words_per_minute'] for r in reading_records]
    avg_wpm = round(sum(wpm_list) / len(wpm_list)) if wpm_list else 0
    max_wpm = max(wpm_list) if wpm_list else 0
    latest_wpm = wpm_list[0] if wpm_list else 0

    # İlerleme trendi
    trend = ''
    if len(wpm_list) >= 2:
        if wpm_list[0] > wpm_list[-1]:
            trend = 'artış'
        elif wpm_list[0] < wpm_list[-1]:
            trend = 'azalış'
        else:
            trend = 'sabit'

    level_info = LEVELS.get(student['level'], LEVELS['baslangic'])
    letter_progress = round(len(learned) / len(TURKISH_ALPHABET) * 100)

    prompt = f"""
Sen bir ilkokul 1. sınıf öğretmenisin. Aşağıdaki verilere göre bir öğrenci için 
kapsamlı, pozitif ve motive edici bir ilerleme raporu yazman gerekiyor.

ÖĞRENCI BİLGİLERİ:
- Ad Soyad: {student['name']}
- Öğrenim Seviyesi: {level_info['label']}
- Notlar: {student.get('notes', 'Yok')}

HARF DURUMU ({len(TURKISH_ALPHABET)} harften):
- Öğrenilen harfler ({len(learned)} adet): {', '.join(learned) if learned else 'Henüz yok'}
- Kısmen öğrenilen ({len(partial)} adet): {', '.join(partial) if partial else 'Yok'}
- Öğrenilmemiş ({len(not_learned)} adet): {', '.join(not_learned) if not_learned else 'Yok'}
- Toplam ilerleme: %{letter_progress}

OKUMA HIZI:
- Son ölçüm: {latest_wpm} kelime/dakika
- Ortalama: {avg_wpm} kelime/dakika
- En yüksek: {max_wpm} kelime/dakika
- Trend: {trend if trend else 'Henüz yeterli ölçüm yok'}
- Toplam ölçüm sayısı: {len(reading_records)}

LÜTFEN RAPORA ŞUNLARI DAHIL ET:
1. 🌟 GENEL DEĞERLENDİRME - Öğrencinin genel durumu (2-3 cümle)
2. 🔤 HARF ÖĞRENME DURUMU - Güçlü ve geliştirilmesi gereken yönler
3. 📖 OKUMA GELİŞİMİ - Okuma hızı değerlendirmesi
4. 💪 GÜÇLÜ YÖNLERİ - Öğrencinin başarıları ve olumlu özellikleri
5. 🎯 GELİŞİM ÖNERİLERİ - Öğretmene ve veliye pratik tavsiyeler (madde madde)
6. 💌 VELİYE MESAJ - Aileye yönelik sıcak, teşvik edici bir mesaj

RAPOR KURALLARI:
- Türkçe yaz
- Çocuk dostu, pozitif ve umut verici bir dil kullan
- Zayıf yönleri nazikçe ve yapıcı şekilde belirt
- Veliye resmi ama sıcak bir dil kullan
- Bölümleri başlıklarla ayır
- Toplam uzunluk: yaklaşık 400-500 kelime

Raporu şimdi yaz:
"""

    if model:
        try:
            if USE_NEW_SDK:
                response = model.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
            else:
                response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return generate_fallback_report(student, learned, partial, not_learned, avg_wpm, latest_wpm, letter_progress)
    else:
        return generate_fallback_report(student, learned, partial, not_learned, avg_wpm, latest_wpm, letter_progress)


def generate_fallback_report(student, learned, partial, not_learned, avg_wpm, latest_wpm, letter_progress):
    """
    AI kullanılamadığında şablon tabanlı rapor üretir.
    """
    level_info = LEVELS.get(student['level'], LEVELS['baslangic'])
    name = student['name']

    learned_str = ', '.join(learned) if learned else 'henüz yok'
    partial_str = ', '.join(partial) if partial else 'yok'
    not_learned_str = ', '.join(not_learned) if not_learned else 'tüm harfler öğrenildi!'

    return f"""
🌟 GENEL DEĞERLENDİRME

{name} adlı öğrencimiz, {level_info['label']} seviyesinde olup Türk alfabesindeki 29 harfin %{letter_progress}'ini başarıyla öğrenmiştir. Öğrencimiz, sınıf içi çalışmalarda gayretli bir tutum sergilemekte ve gelişim göstermektedir.

---

🔤 HARF ÖĞRENME DURUMU

✅ Öğrenilen Harfler ({len(learned)} adet):
{learned_str}

⚠️ Kısmen Öğrenilen Harfler ({len(partial)} adet):
{partial_str}

❌ Çalışılması Gereken Harfler ({len(not_learned)} adet):
{not_learned_str}

Harf öğreniminde %{letter_progress} ilerleme kaydedilmiştir. {'Bu harika bir ilerleme!' if letter_progress >= 70 else 'Düzenli tekrarlarla bu oran hızla artacaktır.'}

---

📖 OKUMA GELİŞİMİ

{name}'in son ölçülen okuma hızı dakikada {latest_wpm} kelimedir. Ortalama okuma hızı ise dakikada {avg_wpm} kelimedir. {'Bu hız, sınıf düzeyi için oldukça iyidir.' if avg_wpm >= 20 else 'Düzenli okuma pratiği ile bu hız önemli ölçüde artacaktır.'}

---

💪 GÜÇLÜ YÖNLERİ

• Öğrenme konusunda istekli ve meraklı bir tutum sergilemektedir.
• Öğrenilen harfleri doğru ve güvenle kullanabilmektedir.
• Sınıf etkinliklerine aktif katılım göstermektedir.

---

🎯 GELİŞİM ÖNERİLERİ

• Her gün en az 10-15 dakika sesli okuma pratiği yapılması önerilir.
• Henüz öğrenilmeyen harfler için tekrar egzersizleri uygulanmalıdır: {not_learned_str[:50]}...
• Flash kart yöntemiyle harf tanıma becerisi pekiştirilmelidir.
• Hece çalışmalarına ağırlık verilmeli, basit kelimeler okunmaya çalışılmalıdır.
• Çocuğun severdiği konulardaki kitaplar okumaya teşvik amacıyla kullanılabilir.

---

💌 VELİYE MESAJ

Sayın Veli,

{name}'in bu dönemdeki gelişimleri değerlendirildiğinde, öğrencimizin Türk alfabesinin %{letter_progress}'ini öğrendiği ve okuma hızının gelişim sürecinde olduğu görülmektedir. Evde yapacağınız kısa süreli okuma çalışmaları, {name}'in ilerlemesine büyük katkı sağlayacaktır. Herhangi bir sorunuz olduğunda lütfen benimle iletişime geçin.

Saygılarımla,
Sınıf Öğretmeni
"""
