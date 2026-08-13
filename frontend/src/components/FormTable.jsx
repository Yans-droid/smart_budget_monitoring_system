import s from './FormTable.module.css'
import { formatRp } from '../utils/format'

const FORMS = [
    { code: 'E-1', type: 'OPEX', color: '#378ADD', cls: 'e1' },
    { code: 'E-9', type: 'OPEX', color: '#e85d3a', cls: 'e9' },
    { code: 'I-1', type: 'CAPEX', color: '#7F77DD', cls: 'i1' },
]

export default function FormTable({ data = {}, onRowClick }) {
    return (
        <div className={s.wrapper}>
            <div className={s.header}>
                <div className={s.headerTitle}>
                    Monitoring per form <span className={s.hint}>— klik baris untuk detail per form</span>
                </div>
                <button
                    className={s.headerDetailBtn}
                    onClick={(e) => { e.stopPropagation(); onRowClick?.('ALL'); }}
                >
                    Detail
                </button>
            </div>

            <div className={s.colHead}>
                <span>Form</span>
                <span>Budget</span>
                <span>Actual</span>
                <span>Saldo</span>
                <span>Pakai</span>
            </div>

            {FORMS.map(f => {
                const d = data[f.code] || { budget: 0, actual: 0, saldo: 0 }
                const pct = d.budget > 0 ? Math.round((d.actual / d.budget) * 100) : 0
                const isOver = pct > 100

                return (
                    <div
                        key={f.code}
                        className={`${s.row} ${isOver ? s.over : ''}`}
                        onClick={() => onRowClick?.(f.code)}
                    >
                        <div className={s.formCell}>
                            <span className={`${s.badge} ${s[f.cls]}`}>{f.code}</span>
                            <span className={s.typeLabel}>{f.type}</span>
                            {isOver && <span className={s.overTag}>Over</span>}
                        </div>

                        <div className={s.numCell}>{formatRp(d.budget)}</div>
                        <div className={`${s.numCell} ${s.warning}`}>{formatRp(d.actual)}</div>
                        <div className={`${s.numCell} ${isOver ? s.danger : s.success}`}>
                            {formatRp(d.saldo)}
                        </div>

                        <div className={s.progWrap}>
                            <div className={s.progBg}>
                                <div
                                    className={s.progBar}
                                    style={{
                                        width: `${Math.min(pct, 100)}%`,
                                        background: isOver ? '#e85d3a' : f.color,
                                    }}
                                />
                            </div>
                            <div className={`${s.progLabel} ${isOver ? s.over : s.normal}`}>
                                {pct}%{isOver ? ' ⚠' : ''}
                            </div>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}