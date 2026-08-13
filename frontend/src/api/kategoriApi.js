import api from './api'

export const kategoriApi = {
  /**
   * Get all kategori
   */
  getAll() {
    return api.get('/kategoris')
      .then(res => res.data)
  },

  /**
   * Get kategori by kode
   * @param {string} kode
   */
  getByKode(kode) {
    return api.get(`/kategoris/kode/${kode}`)
      .then(res => res.data)
  },
}
