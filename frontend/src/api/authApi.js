import api from './api'

export const authApi = {
  /**
   * Login user
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{success, data?, message?, token?}>}
   */
  login(username, password) {
    return api.post('/users/login', { username, password })
      .then(res => {
        const result = res.data
        if (result.success && result.token) {
          localStorage.setItem('token', result.token)
          localStorage.setItem('user', JSON.stringify(result.data))
        }
        return result
      })
  },

  logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },
}