import { useState, useRef } from 'react'
import { planningApi } from '../api/planningApi'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import * as XLSX from 'xlsx'
import styles from './PlanningUpload.module.css'

export default function PlanningUpload() {
  const { user } = useAuth()
  const [file, setFile] = useState(null)
  const [periode, setPeriode] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const pollingRef = useRef(null)

  function validateExcelHeaders(file) {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result)
          const workbook = XLSX.read(data, { type: 'array' })
          const firstSheetName = workbook.SheetNames[0]
          const worksheet = workbook.Sheets[firstSheetName]
          const headers = XLSX.utils.sheet_to_json(worksheet, { header: 1 })[0]
          
          if (!headers) return resolve({ valid: false, message: 'File Excel kosong' })
          
          const normalizedHeaders = headers.map(h => String(h).trim().toLowerCase().replace(/ /g, '_').replace(/-/g, '_'))
          const required = ['month', 'form', 'item', 'planning_amount', 'remarks']
          const missing = required.filter(r => !normalizedHeaders.includes(r))
          
          if (missing.length > 0) {
            resolve({ valid: false, message: `Kolom wajib tidak ditemukan: ${missing.join(', ')}` })
          } else {
            resolve({ valid: true })
          }
        } catch (err) {
          resolve({ valid: false, message: 'Gagal membaca file Excel' })
        }
      }
      reader.readAsArrayBuffer(file)
    })
  }

  function startPolling(planningHeaderId) {
    if (pollingRef.current) clearInterval(pollingRef.current)
    
    pollingRef.current = setInterval(async () => {
      try {
        const res = await planningApi.getById(planningHeaderId)
        const status = res.data?.data?.status
        
        if (status === 'SUCCES') { // The backend spells it SUCCES
          clearInterval(pollingRef.current)
          setLoading(false)
          setResult({
            success: true,
            message: "File berhasil diupload",
            data: {
              planning_header_id: planningHeaderId,
            }
          })
          toast.success('Upload dan pemrosesan Planning selesai!')
        } else if (status === 'FAILED') {
          clearInterval(pollingRef.current)
          setLoading(false)
          toast.error('Gagal memproses file di background')
        }
      } catch (err) {
        clearInterval(pollingRef.current)
        setLoading(false)
        toast.error('Gagal mengecek status upload')
      }
    }, 2000)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) {
      toast.error('Pilih file terlebih dahulu')
      return
    }
    if (!periode) {
      toast.error('Periode wajib diisi')
      return
    }

    const validation = await validateExcelHeaders(file)
    if (!validation.valid) {
      toast.error(validation.message)
      return
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('periode', periode)
    formData.append('user_id', user?.id || 1)

    setLoading(true)
    setResult(null)

    try {
      const res = await planningApi.upload(formData)
      if (res.data?.data?.planning_header_id) {
        toast.success(res.data.message || 'File sedang diproses...')
        startPolling(res.data.data.planning_header_id)
      } else {
        setResult(res.data)
        setLoading(false)
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Upload gagal')
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <h2 className={styles.title}>Upload Planning</h2>

      <div className={styles.card}>
        <form onSubmit={handleSubmit}>
          <label className={styles.label}>Periode *</label>
          <input
            className={styles.input}
            placeholder="cth: 2025"
            value={periode}
            onChange={e => setPeriode(e.target.value)}
            required
            disabled={loading}
          />

          <label className={styles.label}>File Excel *</label>
          <input
            type="file"
            accept=".xls,.xlsx"
            className={styles.fileInput}
            onChange={e => setFile(e.target.files[0])}
            disabled={loading}
          />

          <div className={styles.infoBox}>
            <strong>Format kolom yang dibutuhkan:</strong>
            <br />month, form, item, planning_amount, remarks
          </div>

          <button type="submit" disabled={loading} className={styles.btnPrimary}>
            {loading ? '⏳ Mengupload di Background...' : '📤 Upload Planning'}
          </button>
        </form>
      </div>

      {result?.success && !loading && (
        <div className={styles.successBox}>
          ✅ <strong>Berhasil!</strong> {result.message}
          <br />Planning Header ID: <strong>{result.data?.planning_header_id}</strong>
        </div>
      )}
    </div>
  )
}
