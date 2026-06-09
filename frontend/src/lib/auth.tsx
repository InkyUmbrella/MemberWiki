import { createContext, useContext, useState, useEffect, type ReactNode, useCallback } from "react"
import api from "./api"

interface User {
  id: number
  name: string
  email?: string | null
  phone?: string | null
  avatar_url?: string | null
  role?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (account: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const userId = localStorage.getItem("user_id")
    if (!userId) {
      setLoading(false)
      return
    }
    api.get("/users/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("user_id")
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (account: string, password: string) => {
    const { data } = await api.post("/auth/login", { account, password })
    localStorage.setItem("access_token", data.access_token)
    localStorage.setItem("user_id", String(data.user.id))
    setUser(data.user)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("user_id")
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
