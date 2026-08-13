import { useState, useRef } from 'react'
import { prApi } from '../api/prApi'
import { uploadHistoryApi } from '../api/uploadHistoryApi'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import * as XLSX from 'xlsx'
import styles from './PrUpload.module.css'

export default function PrUpload() {
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
          const required = ['pr_doc_num', 'description', 'request_date']
          const missing = required.filter(r => !normalizedHeaders.includes(r) && !normalizedHeaders.includes('pr_docnum')) // pr_docnum is mapped to pr_doc_num
          
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

  function startPolling(uploadId) {
    if (pollingRef.current) clearInterval(pollingRef.current)
    
    pollingRef.current = setInterval(async () => {
      try {
        const res = await uploadHistoryApi.getById(uploadId)
        const status = res.data?.status
        
        if (status === 'SUCCESS') {
          clearInterval(pollingRef.current)
          setLoading(false)
          setResult({
            success: true,
            data: {
              total_data: res.data.total_data,
              upload_id: uploadId,
              periode
            }
          })
          toast.success('Upload dan pemrosesan PR selesai!')
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
      const res = await prApi.upload(formData)
      if (res.data?.data?.upload_id) {
        toast.success(res.data.message || 'File sedang diproses...')
        startPolling(res.data.data.upload_id)
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
      <h2 className={styles.title}>Upload PR</h2>

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
            <br />pr_doc_num, description, total_price, request_date
            <br /><em>Opsional: po_doc_num, supplier_name, qty, uom, unit_price, dll</em>
          </div>

          <button type="submit" disabled={loading} className={styles.btnPrimary}>
            {loading ? '⏳ Memproses di Background...' : '📤 Upload PR'}
          </button>
        </form>
      </div>

      {result?.success && !loading && (
        <div className={styles.successBox}>
          ✅ <strong>Berhasil!</strong>
          <br />Total PR diproses: <strong>{result.data?.total_data}</strong>
          <br />Upload ID: <strong>{result.data?.upload_id}</strong>
          <br />Periode: <strong>{result.data?.periode}</strong>
          <br /><br />
          <a href="/pr/result" style={{ color: '#166534', fontWeight: 700 }}>→ Lihat Result Matching</a>
        </div>
      )}
    </div>
  )
}
