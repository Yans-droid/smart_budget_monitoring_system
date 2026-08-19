import styles from './SwitchComponent.module.css'

/**
 * Dropdown pilih tahun/periode. Reusable di halaman manapun yang
 * datanya perlu di-scope per tahun (Dashboard, PR History, dst).
 *
 * years: array tahun yang tersedia untuk dipilih, mis. [2026, 2025, 2024]
 * Kalau tidak diberikan, default generate 5 tahun terakhir dari sekarang.
 */
export default function PeriodeSwitcher({ value, onChange, years }) {
    const currentYear = new Date().getFullYear()
    const options = years || Array.from({ length: 5 }, (_, i) => currentYear - i)

    return (
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className={styles.select}
        >
            {options.map((y) => (
                <option key={y} value={String(y)}>
                    {y}
                </option>
            ))}
        </select>
    )
}