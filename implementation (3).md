# BudgetIQ — Implementation Notes: Upload PR & Status Lifecycle Planning

Dokumen ini merangkum desain untuk dua hal: (1) penanganan data PR yang belum lengkap (baru PR, belum sampai PO/GR) saat upload, termasuk pencegahan duplikat saat PR yang sama di-upload ulang; dan (2) status siklus hidup item Planning (`status_realisasi`).

---

## 1. Upload PR — Data Belum Lengkap & Pencegahan Duplikat

### Masalah

File PR yang di-upload sering berisi baris yang datanya belum lengkap — baru sampai tahap PR, belum ada PO apalagi GR. Ada dua sub-masalah yang perlu ditangani terpisah:

**A. Menyimpan baris yang kolom PO/GR/Invoice-nya kosong**

Ini sebenarnya sudah aman di skema — kolom `po_doc_num`, `gr_legal_number`, `receipt_date`, `invoice`, `invoice_date` di `pr_po_data` semuanya nullable. Upload service tinggal simpan `NULL` apa adanya kalau kolom itu kosong di Excel, tidak perlu memaksa isi apa pun.

**B. PR yang sama di-upload ulang setelah progress-nya bertambah**

Skenario nyata: bulan ini upload PR (baru status PR doang, PO/GR kosong), bulan depan upload file yang lebih baru dan PR yang sama sudah ada PO-nya, bahkan sudah GR. Ditemukan lewat pengecekan kode `pr_upload_service.py`: proses upload **selalu `INSERT` baris baru**, tidak ada pengecekan apakah PR tersebut sudah ada di database. Ini menyebabkan baris duplikat — PR yang sama muncul dua kali (yang lama tetap kosong, yang baru lengkap), padahal seharusnya baris yang sama di-**update**.

### Fix — Upsert berbasis `pr_doc_num` + `description`

```python
for _, row in df.iterrows():

    def get(col):
        val = row.get(col)
        return val if pd.notna(val) else None
    # get_date(), get_decimal() tetap sama seperti sebelumnya

    pr_doc_num_val = get("pr_doc_num")
    description_val = get("description")

    existing = PrPoData.query.filter_by(
        pr_doc_num=pr_doc_num_val,
        description=description_val
    ).first()

    if existing:
        # Update kolom procurement yang mungkin bertambah lengkap
        existing.po_doc_num = get("po_doc_num")
        existing.order_date = get_date("order_date")
        existing.supplier_name = get("supplier_name")
        existing.gr_legal_number = get("gr_legal_number")
        existing.packing_slip = get("packing_slip")
        existing.receipt_date = get_date("receipt_date")
        existing.invoice = get("invoice")
        existing.invoice_date = get_date("invoice_date")
        existing.pr_status = get("pr_status")
        existing.po_status = get("po_status")
        existing.qty = get_decimal("qty")
        existing.unit_price = get_decimal("unit_price")
        existing.total_price = get_decimal("total_price")
        existing.upload_id = upload_id  # jejak upload terakhir yang menyentuh baris ini

        # SENGAJA TIDAK disentuh: kategori_id, status_ai, planning_detail_id,
        # perlu_review, kategori_id_koreksi — kalau baris ini sudah DONE
        # (sudah diklasifikasi/dimapping), progress itu tidak boleh hilang
        # hanya karena PO/GR-nya baru terisi belakangan.
    else:
        pr = PrPoData(
            upload_id=upload_id,
            pr_doc_num=pr_doc_num_val,
            description=description_val,
            po_doc_num=get("po_doc_num"),
            requisition_id=get("requisition_id"),
            request_date=get_date("request_date"),
            order_date=get_date("order_date"),
            comment_text=get("comment_text"),
            supplier_name=get("supplier_name"),
            qty=get_decimal("qty"),
            uom=get("uom"),
            unit_price=get_decimal("unit_price"),
            total_price=get_decimal("total_price"),
            gr_legal_number=get("gr_legal_number"),
            packing_slip=get("packing_slip"),
            receipt_date=get_date("receipt_date"),
            invoice=get("invoice"),
            invoice_date=get_date("invoice_date"),
            pr_status=get("pr_status"),
            po_status=get("po_status"),
            status_ai="WAITING"
        )
        db.session.add(pr)

    db.session.flush()
    saved_count += 1
```

**Kenapa `kategori_id`/`status_ai`/`planning_detail_id`/`perlu_review` sengaja tidak disentuh saat update:** kalau baris ini sebelumnya sudah diklasifikasi dan dimapping (status `DONE`), progress itu adalah hasil kerja (otomatis atau manual review) yang sudah tervalidasi. PO/GR yang baru terisi belakangan tidak mengubah *item apa* yang dipesan — jadi tidak ada alasan mengulang klasifikasi/mapping dari nol.

**Nyambung ke `procurement_status` (lihat bagian status tracking lain):** begitu `existing.gr_legal_number` ter-update dari `NULL` jadi terisi, trigger `BEFORE UPDATE` pada `pr_po_data` otomatis menghitung ulang `procurement_status` jadi `GOODS_RECEIVED` — tidak perlu logic tambahan di upload service untuk ini.

### Edge case yang belum ditangani

Kalau dalam satu PR ada dua baris item dengan `description` **persis sama** (misal dipesan 2x terpisah, atau kesalahan input), key `pr_doc_num + description` akan menganggap keduanya sebagai baris yang sama saat upsert. Kalau kasus ini realistis terjadi di data produksi, perlu key tambahan (misal + nomor urut baris dari Excel, atau + qty) untuk membedakan.

---

## 2. Status Lifecycle Item Planning (`status_realisasi`)

### Kebutuhan

Satu item Planning bisa direalisasikan lewat **lebih dari satu PR**, bahkan di bulan yang berbeda (dikonfirmasi dengan admin — tergantung kebutuhan pengadaan). Karena itu, status realisasi per item Planning tidak bisa ditentukan dari satu PR saja, melainkan harus dihitung dari **agregat semua PR** yang `planning_detail_id`-nya mengarah ke item Planning tersebut.

### Definisi status

| Status | Kondisi |
|---|---|
| `OPEN` | Belum ada PR manapun yang di-mapping ke item Planning ini |
| `PROSES` | Ada minimal satu PR yang sudah di-mapping, tapi belum semuanya diterima (`procurement_status` PR tersebut belum `GOODS_RECEIVED`/`COMPLETED`) |
| `CLOSED` | **Semua** PR yang di-mapping ke item Planning ini sudah diterima |

### Skema

```sql
ALTER TABLE planning_detail
ADD COLUMN status_realisasi ENUM('OPEN', 'PROSES', 'CLOSED') NOT NULL DEFAULT 'OPEN';
```

### Trigger — versi agregat (bukan cuma lihat satu baris PR yang lagi diupdate)

Versi awal yang lebih sederhana (hanya melihat baris `NEW` yang sedang di-update) punya risiko: kalau ada dua PR berbeda yang mapping ke item Planning yang sama, trigger versi sederhana bisa "menimpa" status jadi `CLOSED` gara-gara PR yang di-update terakhir kebetulan sudah diterima, padahal PR lain yang juga mapping ke situ belum. Maka dipakai versi agregat:

```sql
DELIMITER $$

CREATE TRIGGER trg_update_planning_status
AFTER UPDATE ON pr_po_data
FOR EACH ROW
BEGIN
    -- Hitung ulang status planning_detail yang di-mapping oleh baris ini
    IF NEW.planning_detail_id IS NOT NULL THEN
        UPDATE planning_detail
        SET status_realisasi = (
            SELECT CASE
                WHEN COUNT(*) = 0 THEN 'OPEN'
                WHEN SUM(CASE WHEN p.procurement_status NOT IN ('GOODS_RECEIVED','COMPLETED') THEN 1 ELSE 0 END) > 0 THEN 'PROSES'
                ELSE 'CLOSED'
            END
            FROM pr_po_data p
            WHERE p.planning_detail_id = NEW.planning_detail_id
        )
        WHERE id = NEW.planning_detail_id;
    END IF;

    -- Kalau planning_detail_id BERUBAH (mis. reviewer mengoreksi mapping),
    -- planning_detail yang LAMA juga harus dihitung ulang karena kehilangan satu PR
    IF OLD.planning_detail_id IS NOT NULL 
       AND (NEW.planning_detail_id IS NULL OR OLD.planning_detail_id != NEW.planning_detail_id) THEN
        UPDATE planning_detail
        SET status_realisasi = (
            SELECT CASE
                WHEN COUNT(*) = 0 THEN 'OPEN'
                WHEN SUM(CASE WHEN p.procurement_status NOT IN ('GOODS_RECEIVED','COMPLETED') THEN 1 ELSE 0 END) > 0 THEN 'PROSES'
                ELSE 'CLOSED'
            END
            FROM pr_po_data p
            WHERE p.planning_detail_id = OLD.planning_detail_id
        )
        WHERE id = OLD.planning_detail_id;
    END IF;
END$$

DELIMITER ;
```

### Catatan performa

Trigger ini menjalankan query agregat (`SELECT ... SUM(...) FROM pr_po_data WHERE planning_detail_id = ...`) setiap kali ada `UPDATE` pada `pr_po_data` yang menyentuh `planning_detail_id`. Untuk skala data sekarang (satu item Planning paling banyak direalisasikan lewat beberapa PR), ini masih ringan. Kalau nanti satu item Planning bisa punya ratusan PR terkait, perlu dipertimbangkan index pada `planning_detail_id` di `pr_po_data` (kemungkinan besar sudah ada karena kolom FK) dan dipantau performanya.

### Status Planning ini beda level dari status lain

Perlu diingat, ada **tiga status berbeda level** yang jangan disamakan satu sama lain:

| Status | Level | Arti |
|---|---|---|
| `status_ai` | per item PR | Progress pipeline klasifikasi+mapping: `WAITING → PROCESSING → DONE / FAILED / NEED_MAPPING / OUT_OF_PLAN` |
| `procurement_status` | per item PR | Progress fisik pengadaan: `PR_CREATED → PO_ISSUED → PARTIAL_RECEIVED/GOODS_RECEIVED → COMPLETED` |
| `status_realisasi` | per item Planning | Progress budget: `OPEN → PROSES → CLOSED` (agregat dari semua PR yang mapping ke situ) |

---

## Belum Diimplementasi (masih desain)

- [ ] Upsert logic pada `pr_upload_service.py` (bagian 1)
- [ ] `ALTER TABLE` + trigger agregat `status_realisasi` pada `planning_detail` (bagian 2)
