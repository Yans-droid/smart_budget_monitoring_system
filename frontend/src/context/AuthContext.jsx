import { createContext, useContext, useState, useCallback } from 'react'
import { authApi } from '../api/authApi'

const AuthContext = createContext(null)

function getStoredUser() {
  try {
    const raw = sessionStorage.getItem('sai_qc_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser)

  const login = useCallback(async (username, password) => {
    try {
      const result = await authApi.login(username, password)

      if (result.success && result.data) {
        const userData = {
          id: result.data.id,
          username: result.data.username,
          role: result.data.role,
          displayName: result.data.username,
        }
        sessionStorage.setItem('sai_qc_user', JSON.stringify(userData))
        setUser(userData)
        return { success: true }
      }

      return { success: false, message: result.message || 'Login gagal' }
    } catch (err) {
      const message =
        err.response?.data?.message ||
        err.message ||
        'Terjadi kesalahan saat login'
      return { success: false, message }
    }
  }, [])

  const logout = useCallback(() => {
    sessionStorage.removeItem('sai_qc_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
