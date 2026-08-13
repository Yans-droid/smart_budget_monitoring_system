import { useState } from 'react'
import s from './AlertBanner.module.css'

export default function AlertBanner({ alerts = [] }) {
  const [dismissed, setDismissed] = useState([])

  const visible = alerts.filter((_, i) => !dismissed.includes(i))
  if (visible.length === 0) return null

  return (
    <div className={s.wrapper}>
      {alerts.map((alert, i) => {
        if (dismissed.includes(i)) return null
        return (
          <div key={i} className={s.banner}>
            <span className={s.icon}>⚠</span>
            <div className={s.content}>
              <span className={s.title}>{alert.title} — </span>
              <span className={s.desc}>{alert.desc}</span>
            </div>
            <button
              className={s.closeBtn}
              onClick={() => setDismissed(prev => [...prev, i])}
              aria-label="Tutup"
            >
              ✕
            </button>
          </div>
        )
      })}
    </div>
  )
}