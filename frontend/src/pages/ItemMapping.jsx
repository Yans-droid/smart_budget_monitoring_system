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

  useEffect(() => { fetchAll() }, [])
  useEffect(() => {
    kategoriApi.getAll().then(d => setKategoris(d.data || [])).catch(() => {})
  }, [])

  async function fetchAll() {
    setLoading(true)
    try {
      const res = await itemMappingApi.getAll()
      setMappings(res.data?.data || [])
    } catch { setError('Gagal memuat data') }
    finally { setLoading(false) }
  }

  function openCreate() { setForm({ keyword: '', planning_item: '', kategori_id: '', priority: 1, is_active: true }); setEditData(null); setShowForm(true) }
  function openEdit(m) { setForm({ keyword: m.keyword, planning_item: m.planning_item, kategori_id: m.kategori_id || '', priority: m.priority, is_active: m.is_active }); setEditData(m); setShowForm(true) }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editData) await itemMappingApi.update(editData.id, form)
      else await itemMappingApi.create(form)
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
                <button type="button" onClick={() => setShowForm(false)} className={styles.btnCancel}>Batal</button>
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
