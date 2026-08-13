import { useState, useEffect } from 'react'
import { prApi } from '../api/prApi'
import { kategoriApi } from '../api/kategoriApi'
import styles from './PrResult.module.css'

const STATUS_CONFIG = {
  PLANNING:  { bg: '#dcfce7', color: '#166534', label: 'PLANNING'  },
  OVER_PLAN: { bg: '#fef9c3', color: '#854d0e', label: 'OVER BUDGET' },
  OOP:       { bg: '#fee2e2', color: '#991b1b', label: 'OOP'       },
}

export default function PrResult() {
  const [prList, setPrList] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [kategoris, setKategoris] = useState([])

  // Filters
  const [filterKategori, setFilterKategori] = useState('')
  const [filterUploadId, setFilterUploadId] = useState('')

  // Summary counts
  const [counts, setCounts] = useState({ PLANNING: 0, OVER_PLAN: 0, OOP: 0 })

  useEffect(() => {
    kategoriApi.getAll().then(d => setKategoris(d.data || [])).catch(() => {})
  }, [])

  useEffect(() => { fetchData() }, [page, filterKategori, filterUploadId])

  async function fetchData() {
    setLoading(true)
    try {
      const params = { page, per_page: 50, status_ai: 'DONE' }
      if (filterKategori) params.kategori_id = filterKategori
      if (filterUploadId) params.upload_id = parseInt(filterUploadId)

      const res = await prApi.getAll(params)
      const d = res.data
      setPrList(d.data || [])
      setTotal(d.total || 0)
      setTotalPages(d.pages || 1)
    } catch { }
    finally { setLoading(false) }
  }

  function fmt(n) {
    if (n == null || n === undefined) return '-'
    return Number(n).toLocaleString('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })
  }

  function StatusBadge({ status }) {
    const cfg = STATUS_CONFIG[status] || { bg: '#f1f5f9', color: '#64748b', label: status }
    return (
      <span style={{ background: cfg.bg, color: cfg.color, borderRadius: 4, padding: '3px 10px', fontSize: 12, fontWeight: 700 }}>
        {cfg.label}
      </span>
    )
  }

  // Count per status from current page (approximation)
  const planningCount = prList.filter(p => p.metode_klasifikasi === 'RULE_BASE' && p.status_ai === 'DONE').length

  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Result Matching</h2>
      <p className={styles.subtitle}>
        Hasil klasifikasi PR: <strong>PLANNING</strong> / <strong>OVER BUDGET</strong> / <strong>OOP</strong>
      </p>

      {/* Filters */}
      <div className={styles.filters}>
        <input
          placeholder="Upload ID"
          value={filterUploadId}
          onChange={e => { setFilterUploadId(e.target.value); setPage(1) }}
          className={styles.input}
        />
        <select value={filterKategori} onChange={e => { setFilterKategori(e.target.value); setPage(1) }} className={styles.input}>
          <option value="">Semua Kategori</option>
          {kategoris.map(k => <option key={k.id} value={k.id}>{k.kode} - {k.nama}</option>)}
        </select>
        <span className={styles.totalLabel}>
          Total PR selesai: <strong>{total}</strong>
        </span>
      </div>

      {/* Table */}
      {loading ? <p>Memuat...</p> : (
        <>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr className={styles.tableHeader}>
                  {['#', 'PR Doc', 'Description', 'Kategori', 'Supplier', 'Total Price', 'Metode', 'Status'].map(h => (
                    <th key={h} className={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {prList.length === 0 && (
                  <tr><td colSpan={8} className={styles.emptyState}>
                    Belum ada hasil matching. Upload PR terlebih dahulu.
                  </td></tr>
                )}
                {prList.map((pr, i) => (
                  <tr key={pr.id} className={styles.tr}>
                    <td className={styles.td}>{(page - 1) * 50 + i + 1}</td>
                    <td className={`${styles.td} ${styles.tdCode}`}>
                      {pr.pr_doc_num || '-'}
                    </td>
                    <td className={`${styles.td} ${styles.tdDesc}`} title={pr.description}>
                      {pr.description || '-'}
                    </td>
                    <td className={styles.td}>{pr.kategori_kode || pr.kategori_id || '-'}</td>
                    <td className={styles.td}>{pr.supplier_name || '-'}</td>
                    <td className={`${styles.td} ${styles.tdRight}`}>{fmt(pr.total_price)}</td>
                    <td className={`${styles.td} ${styles.tdMethod}`}>{pr.metode_klasifikasi || '-'}</td>
                    <td className={styles.td}>
                      {/* Status ditentukan oleh matching engine / budget — tampilkan berdasarkan perlu_review */}
                      {pr.perlu_review
                        ? <span className={styles.badgeReview}>PERLU REVIEW</span>
                        : <StatusBadge status={pr.budget_status === 'ON_PLAN' ? 'PLANNING' : (pr.budget_status || pr.status_ai)} />
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className={styles.pagination}>
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className={styles.pgBtn}>‹ Prev</button>
            <span className={styles.pgLabel}>Hal {page} / {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className={styles.pgBtn}>Next ›</button>
          </div>
        </>
      )}
    </div>
  )
}
