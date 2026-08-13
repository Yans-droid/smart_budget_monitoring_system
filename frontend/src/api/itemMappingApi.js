import api from './api'

export const itemMappingApi = {
  getAll: (params = {}) =>
    api.get('/item-mappings/', { params }),

  getById: (id) =>
    api.get(`/item-mappings/${id}`),

  create: (data) =>
    api.post('/item-mappings/', data),

  update: (id, data) =>
    api.put(`/item-mappings/${id}`, data),

  delete: (id) =>
    api.delete(`/item-mappings/${id}`),
}
