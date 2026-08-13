import { useState, useRef } from 'react'
import * as XLSX from 'xlsx'
import s from './Predict.module.css'
import { classificationApi } from '../api/classificationApi'
import { prPoDataApi } from '../api/prPoDataApi'
import { uploadHistoryApi } from '../api/uploadHistoryApi'
import { useAuth } from '../context/AuthContext'

const PREVIEW_COLS = ['PR DocNum', 'Description', 'Unit Price', 'PR Qty', 'CommentText']

const BADGE_MAP = {
  'E-1': s.badgeE1, 'E-9': s.badgeE9,
  'I-1': s.badgeI1, 'CAPEX': s.badgeCap,
}

const fmt = (n) =>
  n >= 1_000_000_000 ? `Rp ${(n / 1_000_000_000).toFixed(1)} M`
    : n >= 1_000_000 ? `Rp ${(n / 1_000_000).toFixed(1)} Jt`
      : n >= 1_000 ? `Rp ${(n / 1_000).toFixed(0)} Rb`
        : `Rp ${n}`

function getBadge(label) {
  return BADGE_MAP[label] || s.badgeUnk
}

export default function Predict() {
  const { user } = useAuth()
  const [rows, setRows] = useState([])
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [fileName, setFileName] = useState('')
  const [message, setMessage] = useState({ type: '', text: '' })
  const fileRef = useRef()

  const step = results.length > 0 ? 4 : rows.length > 0 ? 2 : 1

  function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return
    setFileName(file.name)
    setResults([])
    setMessage({ type: '', text: '' })
    const reader = new FileReader()
    reader.onload = (evt) => {
      const wb = XLSX.read(evt.target.result, { type: 'binary' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const data = XLSX.utils.sheet_to_json(ws)
      setRows(data)
    }
    reader.readAsBinaryString(file)
  }

  async function handlePredict() {
    if (!rows.length) return
    setLoading(true)
    setMessage({ type: '', text: '' })
    try {
      // Build text items for classification
      const items = rows.map(r => {
        const desc = r['Description'] ?? ''
        const comment = r['CommentText'] ?? ''
        return `${desc} ${comment}`.trim()
      })

      const res = await classificationApi.classifyBulk(items)

      if (res.success && res.data) {
        const merged = rows.map((r, i) => ({
          ...r,
          BudgetCode: res.data[i]?.kode ?? 'UNKNOWN',
          Method: res.data[i]?.method ?? '-',
          Confidence: res.data[i]?.confidence ?? 0,
          Total: (r['Unit Price'] ?? 0) * (r['PR Qty'] ?? 1),
        }))
        setResults(merged)
      } else {
        setMessage({ type: 'error', text: res.message || 'Gagal melakukan prediksi' })
      }
    } catch (err) {
      console.error(err)
      setMessage({ type: 'error', text: err.response?.data?.message || 'Gagal melakukan prediksi' })
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    if (!results.length) return
    setSaving(true)
    setMessage({ type: '', text: '' })

    try {
      // 1. Create upload history
      const uploadRes = await uploadHistoryApi.create({
        filename: fileName,
        total_data: results.length,
        user_id: user?.id,
      })

      const uploadId = uploadRes?.data?.id

      // 2. Bulk save PR/PO data
      const items = results.map(r => ({
        pr_doc_num: r['PR DocNum'] ?? null,
        description: r['Description'] ?? null,
        comment_text: r['CommentText'] ?? null,
        unit_price: r['Unit Price'] ?? null,
        qty: r['PR Qty'] ?? null,
        total_price: r.Total ?? null,
        supplier_name: r['Supplier Name'] ?? null,
      }))

      const bulkRes = await prPoDataApi.createBulk(items, uploadId)

      if (bulkRes.success) {
        // 3. Trigger classification for the uploaded batch
        if (uploadId) {
          try {
            await classificationApi.classifyByUpload(uploadId)
          } catch (classifyErr) {
            console.warn('Auto-classify failed:', classifyErr)
          }
        }

        setMessage({
          type: 'success',
          text: `${bulkRes.total} data berhasil disimpan ke dashboard`,
        })
      } else {
        setMessage({ type: 'error', text: bulkRes.message || 'Gagal menyimpan data' })
      }
    } catch (err) {
      console.error(err)
      setMessage({ type: 'error', text: err.response?.data?.message || 'Gagal menyimpan ke dashboard' })
    } finally {
      setSaving(false)
    }
  }

  const ruleCount = results.filter(r => r.Method === 'RULE_BASE' || r.Method === 'REGEX').length
  const svmCount = results.filter(r => r.Method === 'SVM').length

  return (
    <div className={s.page}>
      <div className={s.header}>
        <h1>Predict budget code</h1>
        <p>Upload file PR/PO untuk prediksi otomatis</p>
      </div>

      {message.text && (
        <div style={{
          padding: '10px 16px',
          borderRadius: 8,
          marginBottom: 16,
          fontSize: 13,
          background: message.type === 'success' ? '#ecfdf5' : '#fef2f2',
          color: message.type === 'success' ? '#065f46' : '#991b1b',
          border: `1px solid ${message.type === 'success' ? '#a7f3d0' : '#fecaca'}`,
        }}>
          {message.type === 'success' ? '✓' : '⚠'} {message.text}
        </div>
      )}

      <div className={s.content}>
        <div className={s.leftPanel}>
          <div className={s.stepCard}>
            <div className={s.stepLabel}>Alur proses</div>
            <div className={s.stepList}>
              {['Upload file', 'Preview data', 'Jalankan prediksi', 'Simpan ke dashboard'].map((label, i) => (
                <div key={i}>
                  <div className={`${s.stepItem} ${step > i ? s.active : ''}`}>
                    <div className={`${s.stepNum} ${step > i + 1 ? s.done : step === i + 1 ? s.active : ''}`}>
                      {step > i + 1 ? '✓' : i + 1}
                    </div>
                    {label}
                  </div>
                  {i < 3 && <div className={s.stepLine} />}
                </div>
              ))}
            </div>
          </div>

          {fileName && (
            <div className={s.fileCard}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8 }}>
                <span style={{ fontSize: 20, color: '#73726c' }}>📊</span>
                <div>
                  <div className={s.fileName}>{fileName}</div>
                  <div className={s.fileMeta}>{rows.length} baris</div>
                </div>
              </div>
              <div className={s.fileTags}>
                <span className={s.fileTag}>✓ Description</span>
                <span className={s.fileTag}>✓ CommentText</span>
              </div>
            </div>
          )}

          <div className={s.uploadZone} onClick={() => fileRef.current.click()}>
            <span className={s.uploadIcon}>⬆</span>
            <div className={s.uploadTitle}>{fileName ? 'Ganti file' : 'Upload file'}</div>
            <div className={s.uploadSub}>.xlsx atau .xls</div>
            <input ref={fileRef} type="file" accept=".xlsx,.xls" style={{ display: 'none' }} onChange={handleFile} />
          </div>
        </div>

        <div className={s.rightPanel}>
          {rows.length > 0 && (
            <div className={s.previewCard}>
              <div className={s.previewHeader}>
                <span className={s.previewLabel}>Preview (5 dari {rows.length} baris)</span>
                <div className={s.previewActions}>
                  <button className="btn-secondary">Filter kolom</button>
                  <button className="btn-primary" onClick={handlePredict} disabled={loading}>
                    {loading ? 'Memproses...' : '⚡ Jalankan prediksi'}
                  </button>
                </div>
              </div>
              <div className={s.tableWrap}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      {PREVIEW_COLS.map(c => <th key={c}>{c}</th>)}
                      <th style={{ textAlign: 'center' }}>Kode</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.slice(0, 5).map((r, i) => (
                      <tr key={i}>
                        <td style={{ color: '#73726c' }}>{i + 1}</td>
                        {PREVIEW_COLS.map(c => (
                          <td key={c} style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {r[c] ?? '—'}
                          </td>
                        ))}
                        <td style={{ textAlign: 'center', color: '#73726c' }}>—</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div className={s.resultCard}>
              <div className={s.resultHeader}>
                <div>
                  <div className={s.resultLabel}>Hasil prediksi — {results.length} baris</div>
                  <div className={s.resultTags}>
                    <span className={s.tagRule}>Rule/Regex: {ruleCount}</span>
                    <span className={s.tagSvm}>SVM: {svmCount}</span>
                  </div>
                </div>
                <button className="btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Menyimpan...' : '💾 Simpan ke dashboard'}
                </button>
              </div>
              <div className={s.tableWrap}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>PR DocNum</th>
                      <th>Description</th>
                      <th style={{ textAlign: 'right' }}>Total</th>
                      <th style={{ textAlign: 'center' }}>Kode</th>
                      <th style={{ textAlign: 'center' }}>Method</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.slice(0, 10).map((r, i) => (
                      <tr key={i}>
                        <td style={{ color: '#73726c' }}>{i + 1}</td>
                        <td style={{ maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {r['PR DocNum']}
                        </td>
                        <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {r['Description']}
                        </td>
                        <td style={{ textAlign: 'right' }}>{fmt(r.Total)}</td>
                        <td style={{ textAlign: 'center' }}>
                          <span className={`${s.badge} ${getBadge(r.BudgetCode)}`}>{r.BudgetCode}</span>
                        </td>
                        <td style={{ textAlign: 'center' }} className={s.methodText}>{r.Method}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}