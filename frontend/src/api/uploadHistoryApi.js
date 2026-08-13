import api from './api'

export const uploadHistoryApi = {
  /**
   * Get all upload histories
   */
  getAll() {
    return api.get('/upload-histories')
      .then(res => res.data)
  },

  /**
   * Get upload history by ID
   * @param {number} id
   */
  getById(id) {
    return api.get(`/upload-histories/${id}`)
      .then(res => res.data)
  },

  /**
   * Create a new upload history record
   * Backend expects: { user_id, filename, total_data }
   * @param {{ filename: string, total_data: number, user_id?: number }} data
   */
  create(data) {
    return api.post('/upload-histories', {
      user_id: data.user_id || data.uploaded_by,
      filename: data.filename || data.file_name,
      total_data: data.total_data || data.total_rows || 0,
    }).then(res => res.data)
  },

  /**
   * Update upload history
   * @param {number} id
   * @param {Object} data
   */
  update(id, data) {
    return api.put(`/upload-histories/${id}`, data)
      .then(res => res.data)
  },

  /**
   * Delete upload history
   * @param {number} id
   */
  delete(id) {
    return api.delete(`/upload-histories/${id}`)
      .then(res => res.data)
  },
}
