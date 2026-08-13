import api from './api'

export const userApi = {
  /**
   * Get all users
   */
  getAll() {
    return api.get('/users/').then(res => res.data)
  },

  /**
   * Create a new user
   * @param {{ username: string, password: string, role: 'admin' | 'manager' }} data
   */
  create(data) {
    return api.post('/users/', data).then(res => res.data)
  },

  /**
   * Update user
   * @param {number} id
   * @param {Object} data
   */
  update(id, data) {
    return api.put(`/users/${id}`, data).then(res => res.data)
  },

  /**
   * Delete user
   * @param {number} id
   */
  delete(id) {
    return api.delete(`/users/${id}`).then(res => res.data)
  },
}
