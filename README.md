# Library Management System

Aplikasi ini saya buat untuk mengelola data perpustakaan secara sederhana. 
Fitur utamanya mencakup pengelolaan buku, anggota, peminjaman, dan 
pengembalian buku. Kalau ada buku yang dikembalikan terlambat, 
sistem otomatis menghitung denda Rp1.000 per hari.

Dibangun dengan Python (Flask) dan SQLite.

---

## Cara Menjalankan Aplikasi

Pastikan Python 3.9+ sudah terinstall.

```bash
# Clone repository
git clone https://github.com/Nicholasskusuma/Library_Project.git
cd Library_Project

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Jalankan server
flask --app "app:create_app()" run
```

Server akan berjalan di `http://127.0.0.1:5000`.

---

## Cara Menjalankan Test

```bash
# Jalankan semua test sekaligus dengan laporan coverage
pytest tests/ --cov=app --cov-report=term-missing -v
```

Kalau mau jalankan secara terpisah:

```bash
pytest tests/test_unit.py -v
pytest tests/test_integration.py -v
```

---

## Strategi Pengujian

Pengujian dibagi jadi dua lapisan.

**Unit Test (26 test case)** — menguji fungsi-fungsi kecil secara 
terisolasi, seperti validasi format ISBN, validasi email dan nomor 
telepon, serta perhitungan denda keterlambatan.

**Integration Test (15 test case)** — menguji alur yang lebih lengkap 
melibatkan database dan HTTP request, seperti proses peminjaman buku 
dari awal sampai pengembalian, termasuk kasus-kasus error seperti 
buku habis stok atau anggota tidak ditemukan.

Total coverage yang dicapai 94%, diukur menggunakan pytest-cov.

ini contoh