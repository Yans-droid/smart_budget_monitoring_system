import api from './api'

export const prPoDataApi = {
  /**
   * Get all PR/PO data with pagination and filters
   * @param {{ page?: number, per_page?: number, upload_id?: number, status_ai?: string, perlu_review?: boolean }} [params]
   */
  getAll(params = {}) {
    return api.get('/pr-po-data', { params })
      .then(res => res.data)
  },

  /**
   * Get PR/PO data by ID
   * @param {number} id
   */
  getById(id) {
    return api.get(`/pr-po-data/${id}`)
      .then(res => res.data)
  },

  /**
   * Get data by upload batch
   * @param {number} uploadId
   */
  getByUpload(uploadId) {
    return api.get(`/pr-po-data/upload/${uploadId}`)
      .then(res => res.data)
  },

  /**
   * Get data that needs manual review
   * @param {{ page?: number, per_page?: number }} [params]
   */
  getReviewQueue(params = {}) {
    return api.get('/pr-po-data/review-queue', { params })
      .then(res => res.data)
  },

  /**
   * Get monthly summary for charts
   * @param {string} [periode]
   * @param {string} [kode]
   */
  getMonthlySummary(periode, kode) {
    return api.get('/pr-po-data/monthly-summary', {
      params: { periode, kode },
    }).then(res => res.data)
  },

  /**
   * Create a single PR/PO record
   * @param {Object} data
   */
  create(data) {
    return api.post('/pr-po-data', data)
      .then(res => res.data)
  },

  /**
   * Create multiple PR/PO records (bulk)
   * @param {Object[]} items
   * @param {number} [uploadId]
   */
  createBulk(items, uploadId) {
    return api.post('/pr-po-data/bulk', {
      items,
      upload_id: uploadId,
    }).then(res => res.data)
  },

  /**
   * Update a PR/PO record
   * @param {number} id
   * @param {Object} data
   */
  update(id, data) {
    return api.put(`/pr-po-data/${id}`, data)
      .then(res => res.data)
  },

  /**
   * Review and correct a PR/PO record manually
   * @param {number} id
   * @param {{ kategori_id_koreksi: number, direview_oleh?: number }} data
   */
  review(id, data) {
    return api.put(`/pr-po-data/${id}/review`, data)
      .then(res => res.data)
  },

  /**
   * Approve classification as-is (no category change)
   * @param {number} id
   * @param {{ direview_oleh?: number }} data
   */
  approve(id, data = {}) {
    return api.put(`/pr-po-data/${id}/approve`, data)
      .then(res => res.data)
  },

  /**
   * Delete a PR/PO record
   * @param {number} id
   */

  delete(id) {
    return api.delete(`/pr-po-data/${id}`)
      .then(res => res.data)
  },
}
