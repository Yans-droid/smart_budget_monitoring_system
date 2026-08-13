import api from './api'

export const planningApi = {
  // Upload Excel Planning
  upload: (formData) =>
    api.post('/planning/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }),

  // List semua PlanningHeader
  getAll: (params = {}) =>
    api.get('/planning/', { params }),

  // Detail satu header
  getById: (id) =>
    api.get(`/planning/${id}`),

  // Detail items (per bulan & item)
  getDetails: (id, params = {}) =>
    api.get(`/planning/${id}/details`, { params }),

  // Delete Planning
  delete: (id) =>
    api.delete(`/planning/${id}`),
}
