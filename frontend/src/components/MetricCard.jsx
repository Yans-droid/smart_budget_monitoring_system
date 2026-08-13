import s from './MetricCard.module.css'

export default function MetricCard({ label, value, sub, variant = 'default', onClick }) {
    return (
        <div 
            className={`${s.card} ${s[variant] || ''} ${onClick ? s.clickable : ''}`}
            onClick={onClick}
        >
            <div className={`${s.label} ${s[variant] || ''}`}>
                {label}
            </div>
            <div className={`${s.value} ${s[variant] || ''}`}>
                {value}
            </div>
            {sub && (
                <div className={`${s.sub} ${s[variant] || ''}`}>
                    {sub}
                </div>
            )}
        </div>
    )
}