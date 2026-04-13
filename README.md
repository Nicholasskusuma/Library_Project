# 📚 Library Management System

Aplikasi REST API sederhana untuk manajemen perpustakaan, dibangun dengan Python (Flask) dan SQLite. Mencakup manajemen buku, anggota, peminjaman, dan kalkulasi denda otomatis.

---

## Fitur Utama

| Fitur | Deskripsi |
|---|---|
| **Manajemen Buku** | Tambah, lihat, update, dan hapus data buku beserta stok |
| **Manajemen Anggota** | Registrasi dan kelola data anggota perpustakaan |
| **Peminjaman & Pengembalian** | Catat transaksi peminjaman, update stok otomatis |
| **Kalkulasi Denda** | Hitung denda keterlambatan (Rp 1.000/hari) secara otomatis |

---

## 🚀 Cara Menjalankan Aplikasi

### Prasyarat
- Python 3.11+

### Langkah

```bash
# 1. Clone repository
git clone https://github.com/<username>/library_project.git
cd library_project

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Jalankan server
flask --app "app:create_app()" run
```

Server berjalan di `http://127.0.0.1:5000`.

### Contoh Request

```bash
# Tambah buku
curl -X POST http://localhost:5000/api/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Clean Code","author":"Robert Martin","isbn":"9780132350884"}'

# Tambah anggota
curl -X POST http://localhost:5000/api/members \
  -H "Content-Type: application/json" \
  -d '{"name":"Budi","email":"budi@example.com"}'

# Buat pinjaman (7 hari)
curl -X POST http://localhost:5000/api/loans \
  -H "Content-Type: application/json" \
  -d '{"book_id":1,"member_id":1,"loan_days":7}'

# Kembalikan buku
curl -X POST http://localhost:5000/api/loans/1/return

# Cek denda
curl http://localhost:5000/api/loans/1/fine
```

---

## 🧪 Cara Menjalankan Test

```bash
# Jalankan semua test dengan laporan coverage
pytest tests/ --cov=app --cov-report=term-missing -v

# Hanya unit test
pytest tests/test_unit.py -v

# Hanya integration test
pytest tests/test_integration.py -v
```

### Ringkasan Test

| Jenis | File | Jumlah |
|---|---|---|
| Unit Test | `tests/test_unit.py` | 26 test case |
| Integration Test | `tests/test_integration.py` | 15 test case |
| **Total** | | **41 test case** |

---

## 🔬 Strategi Pengujian

### 1. Unit Testing
Menguji komponen terkecil secara terisolasi tanpa ketergantungan eksternal:
- **Validasi ISBN** – format 10/13 digit, dengan/tanpa tanda hubung
- **Validasi email & nomor telepon** – format yang benar dan salah
- **Logika denda** – perhitungan hari keterlambatan × tarif, dengan return date maupun tanpa
- **`is_overdue()`** – kondisi tepat waktu vs terlambat
- **`to_dict()`** – serialisasi model ke dictionary

### 2. Integration Testing
Menguji interaksi antar komponen (endpoint → service → database):
- **CRUD Buku & Anggota** – tambah, baca, update, hapus via HTTP
- **Validasi input di endpoint** – field kosong, ISBN duplikat, email duplikat
- **Alur peminjaman end-to-end** – pinjam → cek stok → kembalikan → cek stok normal kembali
- **Error handling** – buku habis, buku/anggota tidak ditemukan, pengembalian ganda
- **Endpoint denda** – kalkulasi denda melalui API

### 3. Coverage Target
Target minimal **60% coverage** (aktual biasanya 80%+).

---

## CI/CD – GitHub Actions

Pipeline berjalan otomatis pada setiap **push** dan **pull request** ke semua branch.

**Langkah pipeline:**
1. Checkout kode
2. Setup Python 3.11
3. Install dependencies (`pip install -r requirements.txt`)
4. Jalankan seluruh test + generate laporan coverage (`pytest --cov`)
5. Upload `coverage.xml` sebagai artifact

Lihat konfigurasi di `.github/workflows/ci.yml`.

---

## 🏗️ Struktur Repository

```
library_project/
├── .github/
│   └── workflows/
│       └── ci.yml          # Konfigurasi GitHub Actions
├── app/
│   ├── __init__.py         # App factory (create_app)
│   ├── models.py           # Model: Book, Member, Loan
│   └── routes.py           # Blueprint endpoint REST API
├── tests/
│   ├── test_unit.py        # 26 unit test
│   └── test_integration.py # 15 integration test
├── .gitignore
├── README.md
└── requirements.txt
```