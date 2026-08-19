# Smart Budget Monitoring System (BudgetIQ)

Sistem monitoring budget QC berbasis web yang mengotomatisasi klasifikasi dan pemetaan dokumen Purchase Requisition (PR) terhadap rencana anggaran (Planning), dengan pelacakan status pengadaan end-to-end dari PR hingga barang diterima.

Dibangun untuk **PT Summit Adyawinsa Indonesia**.

Repo: [github.com/Yans-droid/smart_budget_monitoring_system](https://github.com/Yans-droid/smart_budget_monitoring_system)

---

## Daftar Isi

- [Latar Belakang](#latar-belakang)
- [Fitur Utama](#fitur-utama)
- [Tech Stack](#tech-stack)
- [Arsitektur](#arsitektur)
- [Struktur Project](#struktur-project)
- [Instalasi](#instalasi)
- [Environment Variables](#environment-variables)
- [Struktur Database](#struktur-database)
- [Alur Kerja Utama](#alur-kerja-utama)
- [Status Pengembangan](#status-pengembangan)

---

## Latar Belakang

Proses monitoring realisasi anggaran QC secara manual — mencocokkan setiap item PR/PO terhadap Planning bulanan, memantau statusnya dari pengajuan hingga barang diterima — memakan waktu dan rawan human error, terutama saat volume transaksi tinggi. BudgetIQ dibangun untuk mengotomatisasi proses ini secara end-to-end: dari klasifikasi kategori anggaran, pencocokan item ke Planning, pelacakan status procurement, hingga pengelolaan siklus hidup budget itu sendiri.

## Fitur Utama

### Klasifikasi Kategori Anggaran Hybrid 3-Layer
Setiap item PR diklasifikasikan ke kategori anggaran melalui tiga lapis, dari yang paling pasti ke yang paling probabilistik:
1. **Layer 1 — Regex** (`ai/regex_engine.py`) — mendeteksi kode Form eksplisit (I-1/E-1/E-9) atau jenis barang yang sudah dikenal (mis. tools/perkakas), langsung dengan confidence 1.0. Ada pengecualian untuk jasa perbaikan (kata seperti "repair"/"service") agar tidak salah diklasifikasikan sebagai pembelian aset baru.
2. **Layer 2 — Rule Base** (`ai/rule_base.py`) — fallback berbasis skor keyword CAPEX vs OPEX, hanya berjalan jika Layer 1 gagal menentukan Form.
3. **Layer 3 — SVM (TF-IDF)** — fallback terakhir menggunakan model machine learning untuk kasus yang tidak tertangkap dua layer sebelumnya--->Terbatas hanya untuk Form E-1 dan E-9 karena keterbatasan jumlah data untuk Form I-1.

Setiap hasil klasifikasi tercatat lengkap dengan layer, metode, dan confidence score di `klasifikasi_log`.

### Item Mapping ke Planning
Mencocokkan item PR yang sudah terklasifikasi ke item Planning yang sesuai:
- **Rule-based exact match** — dictionary keyword → item Planning, termasuk untuk kategori anggaran umum/catch-all (mis. budget maintenance umum yang realisasinya bisa berupa berbagai jenis barang, dicocokkan lewat kata kunci di catatan PR)
- **Fuzzy matching** (RapidFuzz `token_set_ratio` dengan normalisasi teks) — menghasilkan Top-5 kandidat untuk direview, dengan fallback lintas-bulan untuk PR yang diajukan lebih awal dari jadwal realisasi Planning
- **Deteksi mismatch kode/nomor register** — memberi peringatan saat kandidat fuzzy punya kemiripan teks tinggi tapi kode part/nomor register berbeda
- **Pencarian manual** — search bebas ke seluruh item Planning dalam satu tahun anggaran, untuk kasus yang tidak tertangkap fuzzy matching
- **Tandai Out of Plan (OOP)** — untuk item yang dipastikan tidak ada padanannya di Planning
- **Undo / pembatalan keputusan** — mengembalikan item yang salah dikonfirmasi (termasuk salah tandai OOP) ke antrian review, dengan jejak lengkap di `mapping_log` (tidak menimpa histori lama)

Fuzzy matching **tidak pernah** otomatis mengubah status menjadi selesai walau skor kemiripan tinggi — selalu menunggu konfirmasi manual, kecuali lewat rule-based match yang sudah tervalidasi.

### Pelacakan Status Procurement End-to-End
Setiap item PR memiliki `procurement_status` (`PR_CREATED` → `PO_ISSUED` → `GOODS_RECEIVED` → `COMPLETED`) yang dihitung otomatis via database trigger berdasarkan kelengkapan data (nomor PO, nomor GR, invoice). Upload ulang file PR yang progresnya bertambah (mis. PO baru terbit) akan meng-update baris yang sama, bukan membuat duplikat.

### Siklus Hidup Budget Planning
Setiap item Planning memiliki `status_realisasi`:
- **OPEN** — belum ada PR yang di-mapping ke situ
- **PROSES** — ada PR terkait, tapi belum semuanya diterima
- **CLOSED** — semua PR terkait sudah diterima
- **CANCELLED** — budget dibatalkan secara sah (bukan salah input); hanya bisa dilakukan selama belum ada PR yang di-mapping ke item tersebut, untuk menjaga integritas data — pembatalan ditolak jika masih ada realisasi yang terkait

Status ini dihitung sebagai agregat dari seluruh PR yang terkait ke satu item Planning (satu item Planning bisa direalisasikan lewat lebih dari satu PR, termasuk lintas bulan).

### Autentikasi & Otorisasi
Login berbasis JWT (masa berlaku 8 jam). Aksi yang mengubah keputusan sistem (konfirmasi mapping, undo, pembatalan budget) dibatasi untuk role `admin`.

### Dashboard & Monitoring
- Ringkasan realisasi vs rencana anggaran per kategori (ON_PLAN / OVER_PLAN / UNDER_PLAN / Out of Plan / Cancelled)
- Breakdown bulanan
- Pelacakan tahapan dokumen (PR / PO / GR)
- Export laporan ke PDF

## Tech Stack

| Layer | Teknologi |
|---|---|
| Backend | Python (Flask) |
| Frontend | React (Vite) |
| Database | MySQL 8.0 |
| Autentikasi | JWT (PyJWT) |
| Klasifikasi ML | Scikit-learn (SVM + TF-IDF) |
| Fuzzy Matching | RapidFuzz |
| Container | Docker Compose |
| Charting | Recharts |
| PDF Export | jsPDF |
| Notifikasi | react-hot-toast + dialog konfirmasi custom |

## Arsitektur

```
Upload PR (Excel)
     ↓
Klasifikasi Kategori (Layer 1 Regex → Layer 2 Rule Base → Layer 3 SVM)
     ↓
Item Mapping ke Planning (Rule-Based → Fuzzy Matching → Manual Review/Search)
     ↓
Perhitungan Budget Status (ON_PLAN / OVER_PLAN / UNDER_PLAN / OOP)
     ↓
Pelacakan Status Procurement (PR → PO → GR → Invoice) via DB Trigger
     ↓
Status Realisasi Planning (agregat seluruh PR terkait, termasuk CANCELLED) via Service
     ↓
Dashboard & Laporan
```

Backend dipisah antara **HTTP layer** (`routes/`) dan **business logic** (`services/`), agar logic tetap dapat digunakan di luar konteks HTTP dan mudah diuji terpisah. Aksi manual di Review Mapping (confirm, undo, search) dipisah lagi dari algoritma matching (`advanced_mapping_service.py`) ke service tersendiri, karena keduanya punya alasan berbeda untuk berubah.

## Struktur Project

```
.
├── docker-compose.yml
├── backend/
│   ├── app.py                      # Entry point Flask
│   ├── config.py
│   ├── ai/                         # Model & logic klasifikasi
│   │   ├── models/svm_model.pkl
│   │   ├── predict.py
│   │   ├── preprocess.py
│   │   ├── regex_engine.py         # Layer 1 — deteksi Form
│   │   └── rule_base.py            # Layer 2 — CAPEX/OPEX keyword
│   ├── database/
│   │   ├── schema.sql
│   │   ├── seed.py
│   │   └── seeders/
│   ├── models/                     # SQLAlchemy models
│   ├── routes/                     # HTTP layer (tipis, panggil service)
│   ├── services/                   # Business logic
│   │   ├── mapping/                # Klasifikasi & item mapping
│   │   ├── planning/                # Upload, detail, & pembatalan Planning
│   │   └── pr/                     # Upload & pengelolaan PR
│   ├── utils/
│   │   ├── auth.py                 # JWT generate/decode, decorator role
│   │   ├── db.py
│   │   └── logger.py
│   └── tests/
└── frontend/
    ├── src/
    │   ├── api/                    # Axios instance & fungsi per-domain
    │   ├── components/             # Modal, card, chart, dialog konfirmasi
    │   ├── context/                # AuthContext
    │   ├── pages/                  # Halaman per-route
    │   └── App.jsx
    └── vite.config.js
```

## Instalasi

### Opsi A — Docker Compose (disarankan)

```bash
git clone https://github.com/Yans-droid/smart_budget_monitoring_system.git
cd smart_budget_monitoring_system

cp backend/.env.example backend/.env   # isi kredensial & JWT secret
docker-compose up -d
```

### Opsi B — Manual

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env      # isi kredensial & JWT secret
mysql -u root -p < database/schema.sql
python database/seed.py   # opsional, seed data awal

python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Buat file `.env` di folder `backend/` (jangan pernah di-commit ke repository):

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=db_sai_qc
DB_USER=root
DB_PASSWORD=

JWT_SECRET_KEY=<generate dengan: python3 -c "import secrets; print(secrets.token_hex(32))">
```

## Struktur Database

| Tabel | Keterangan |
|---|---|
| `pr_po_data` | Data realisasi PR/PO, hasil klasifikasi, hasil mapping, `procurement_status` |
| `planning_header` / `planning_detail` | Rencana anggaran per periode, `status_realisasi` (OPEN/PROSES/CLOSED/CANCELLED) |
| `kategori` | Master kategori anggaran (kode Form, tipe CAPEX/OPEX) |
| `klasifikasi_log` | Histori klasifikasi per layer dengan confidence score |
| `mapping_log` | Histori pencocokan item ke Planning (rule/fuzzy/manual), termasuk pembatalan |
| `item_mapping` | Rule dictionary keyword → item Planning |
| `budget` | Alokasi anggaran per kategori dan periode |
| `upload_history` | Riwayat upload file Excel |
| `users` | Akun pengguna dengan role-based access |

Skema lengkap tersedia di `backend/database/schema.sql`.

## Alur Kerja Utama

**1. Upload & Klasifikasi**
Admin upload file Excel PR → tiap baris disimpan dengan status `WAITING` → dijalankan pipeline klasifikasi (3 layer) → `kategori_id` terisi.

**2. Item Mapping**
Sistem mencari padanan di Planning: rule-based dulu (langsung `DONE` jika cocok), lalu fuzzy matching (Top-5 kandidat, status `NEED_MAPPING`). Reviewer mengonfirmasi dari Top-5, mencari manual, atau menandai OOP.

**3. Budget Monitoring**
Setelah ter-mapping, sistem membandingkan realisasi terhadap `planning_amount` → `budget_status` (ON_PLAN/OVER_PLAN/UNDER_PLAN).

**4. Pelacakan Procurement**
Saat file PR yang sama di-upload ulang dengan data PO/GR yang lebih lengkap, `procurement_status` ter-update otomatis via trigger, dan `status_realisasi` item Planning terkait ikut dihitung ulang.

**5. Koreksi**
Kalau ada kesalahan konfirmasi mapping, gunakan Undo untuk mengembalikan ke antrian review. Kalau ada budget yang perlu dibatalkan (bukan salah input, tapi keputusan bisnis yang sah), gunakan fitur Batalkan Item Planning — selama belum ada PR yang terealisasi ke situ.

## Status Pengembangan

Proyek ini masih dalam tahap pengembangan aktif.

## Lisensi

Internal — PT Summit Adyawinsa Indonesia.
