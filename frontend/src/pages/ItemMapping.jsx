import toast from 'react-hot-toast'

import { useState, useEffect } from 'react'
import { itemMappingApi } from '../api/itemMappingApi'
import { kategoriApi } from '../api/kategoriApi'
import styles from './ItemMapping.module.css'

export default function ItemMapping() {
  const [mappings, setMappings] = useState([])
  const [kategoris, setKategoris] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editData, setEditData] = useState(null)
  const [form, setForm] = useState({ keyword: '', planning_item: '', kategori_id: '', priority: 1, is_active: true })
  const [suggestions, setSuggestions] = useState([])
  // keyword saran yang sedang diproses lewat form (agar bisa dihapus dari list setelah simpan)
  const [appliedKeyword, setAppliedKeyword] = useState(null)

  useEffect(() => { fetchAll() }, [])
  useEffect(() => {
    kategoriApi.getAll().then(d => setKategoris(d.data || [])).catch(() => { })
  }, [])
  useEffect(() => {
    itemMappingApi.getSuggestions()
      .then(res => setSuggestions(res.data?.data || []))
      .catch(() => { /* suggestion opsional, silent fail ok */ })
  }, [])
  function applySuggestion(s) {
    setAppliedKeyword(s.description)  // simpan keyword untuk filter ulang saat disubmit
    setForm({ keyword: s.description, planning_item: s.planning_item, kategori_id: '', priority: 1, is_active: true })
    setEditData(null)
    setShowForm(true)
  }

  function dismissSuggestion(s) {
    // Hapus optimistis dulu dari UI, lalu simpan sebagai inactive ke backend
    setSuggestions(prev => prev.filter(x => x.description !== s.description))
    itemMappingApi.create({
      keyword: s.description,
      planning_item: s.planning_item,
      kategori_id: null,
      priority: 1,
      is_active: false
    }).catch(() => {
      // Kalau gagal simpan, tampilkan toast (saran sudah hilang dari UI, tidak masalah)
      toast.error('Gagal menyimpan dismiss — saran akan muncul lagi setelah refresh')
    })
  }

  async function fetchAll() {
    setLoading(true)
    try {
      const res = await itemMappingApi.getAll()
      setMappings(res.data?.data || [])
    } catch { setError('Gagal memuat data') }
    finally { setLoading(false) }
  }

  function closeForm() {
    setShowForm(false)
    setAppliedKeyword(null)
  }

  function openCreate() { setForm({ keyword: '', planning_item: '', kategori_id: '', priority: 1, is_active: true }); setEditData(null); setShowForm(true) }
  function openEdit(m) { setForm({ keyword: m.keyword, planning_item: m.planning_item, kategori_id: m.kategori_id || '', priority: m.priority, is_active: m.is_active }); setEditData(m); setShowForm(true) }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editData) {
        await itemMappingApi.update(editData.id, form)
        toast.success('Rule berhasil diupdate')
      } else {
        await itemMappingApi.create(form)
        toast.success('Rule berhasil disimpan')
        // Hapus saran dari list jika form ini berasal dari saran
        if (appliedKeyword) {
          setSuggestions(prev => prev.filter(x => x.description !== appliedKeyword))
          setAppliedKeyword(null)
        }
      }
      setShowForm(false)
      fetchAll()
    } catch { toast.error('Gagal menyimpan') }
  }

  async function handleDelete(id) {
    if (!confirm('Hapus mapping ini?')) return
    try { await itemMappingApi.delete(id); fetchAll() }
    catch { toast.error('Gagal menghapus') }
  }

  const statusBadge = (active) => (
    <span className={active ? styles.badgeActive : styles.badgeInactive}>
      {active ? 'Aktif' : 'Nonaktif'}
    </span>
  )

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2 className={styles.title}>Item Mapping</h2>
        <button onClick={openCreate} className={styles.btnPrimary}>+ Tambah Mapping</button>
      </div>

      {error && <p className={styles.error}>{error}</p>}
      {suggestions.length > 0 && (
        <div className={styles.suggestionPanel}>
          <h3 className={styles.suggestionTitle}>💡 Saran Rule dari Histori ({suggestions.length})</h3>
          {suggestions.map((s, i) => (
            <div key={i} className={styles.suggestionRow}>
              <span>"{s.description}" → <strong>{s.planning_item}</strong> <em style={{ color: '#6b7280' }}>({s.jumlah_kemunculan}x dipilih)</em></span>
              <div className={styles.suggestionActions}>
                <button onClick={() => applySuggestion(s)} className={styles.btnPrimarySm}>+ Jadikan Rule</button>
                <button onClick={() => dismissSuggestion(s)} className={styles.btnCancelSm}>Abaikan</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <div className={styles.overlay}>
          <div className={styles.modal}>
            <h3 className={styles.modalTitle}>{editData ? 'Edit' : 'Tambah'} Item Mapping</h3>
            <form onSubmit={handleSubmit}>
              <label className={styles.label}>Keyword *</label>
              <input className={styles.input} value={form.keyword} onChange={e => setForm({ ...form, keyword: e.target.value })} required />

              <label className={styles.label}>Planning Item *</label>
              <input className={styles.input} value={form.planning_item} onChange={e => setForm({ ...form, planning_item: e.target.value })} required />

              <label className={styles.label}>Kategori</label>
              <select className={styles.input} value={form.kategori_id} onChange={e => setForm({ ...form, kategori_id: e.target.value })}>
                <option value="">-- Semua Kategori --</option>
                {kategoris.map(k => <option key={k.id} value={k.id}>{k.kode} - {k.nama}</option>)}
              </select>

              <label className={styles.label}>Priority</label>
              <input type="number" className={styles.input} value={form.priority} min={1} onChange={e => setForm({ ...form, priority: parseInt(e.target.value) })} />

              <label className={`${styles.label} ${styles.checkboxLabel}`}>
                <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} /> Aktif
              </label>

              <div className={styles.actionRow}>
                <button type="submit" className={styles.btnPrimary}>Simpan</button>
                <button type="button" onClick={closeForm} className={styles.btnCancel}>Batal</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? <p>Memuat...</p> : (
        <table className={styles.table}>
          <thead>
            <tr className={styles.tableHeader}>
              {['#', 'Keyword', 'Planning Item', 'Kategori', 'Priority', 'Status', 'Aksi'].map(h => (
                <th key={h} className={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mappings.length === 0 && <tr><td colSpan={7} className={styles.emptyState}>Belum ada data</td></tr>}
            {mappings.map((m, i) => (
              <tr key={m.id} className={styles.tr}>
                <td className={styles.td}>{i + 1}</td>
                <td className={styles.td}>{m.keyword}</td>
                <td className={styles.td}>{m.planning_item}</td>
                <td className={styles.td}>{m.kategori_id || '-'}</td>
                <td className={styles.td}>{m.priority}</td>
                <td className={styles.td}>{statusBadge(m.is_active)}</td>
                <td className={styles.td}>
                  <button onClick={() => openEdit(m)} className={styles.btnEdit}>Edit</button>
                  {' '}
                  <button onClick={() => handleDelete(m.id)} className={styles.btnDelete}>Hapus</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
