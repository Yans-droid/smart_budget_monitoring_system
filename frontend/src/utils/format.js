export const formatRp = (n) => {
    if (n === null || n === undefined || isNaN(n)) return 'Rp 0';
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n);
};
