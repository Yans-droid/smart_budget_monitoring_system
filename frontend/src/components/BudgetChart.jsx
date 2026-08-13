import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer
} from 'recharts'
import s from './BudgetChart.module.css'

import { formatRp } from '../utils/format'

const COLORS = {
    actual: '#3B82F6',
    saldo: '#10B981',
    budget: '#CBD5E1',
}

const fmtYAxis = (v) => {
    if (v >= 1000) return `Rp ${(v / 1000).toFixed(0)}K`
    return `Rp ${v}`
}

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className={s.tooltip}>
                <div className={s.tooltipLabel}>{label}</div>
                {payload.map(p => (
                    <div key={p.name} style={{ color: p.dataKey === 'budget' ? '#64748B' : p.fill }}>
                        {p.name}: {formatRp(p.value)}
                    </div>
                ))}
            </div>
        )
    }
    return null
}

export default function BudgetChart({ title, data = [] }) {
    const legends = [
        { label: 'Actual', color: COLORS.actual },
        { label: 'Saldo', color: COLORS.saldo },
        { label: 'Budget', color: COLORS.budget },
    ]

    return (
        <div className={s.wrapper}>
            <div className={s.header}>
                <div className={s.title}>{title}</div>
                <div className={s.legend}>
                    {legends.map(({ label, color }) => (
                        <div key={label} className={s.legendItem}>
                            <div
                                className={s.legendColorBox}
                                style={{ background: color }}
                            />
                            <span>{label}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className={s.chartArea}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} barCategoryGap="30%" barGap={3}>
                        <CartesianGrid vertical={false} stroke="rgba(0,0,0,0.06)" />
                        <XAxis
                            dataKey="name"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 12, fill: '#73726c' }}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 11, fill: '#73726c' }}
                            tickFormatter={fmtYAxis}
                            width={80}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="actual" fill={COLORS.actual} radius={[4, 4, 0, 0]} maxBarSize={40} />
                        <Bar dataKey="saldo" fill={COLORS.saldo} radius={[4, 4, 0, 0]} maxBarSize={40} />
                        <Bar dataKey="budget" fill={COLORS.budget} radius={[4, 4, 0, 0]} maxBarSize={40} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}