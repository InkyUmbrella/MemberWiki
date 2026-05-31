import axios from "axios"

const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
})

// 请求拦截器：自动附加 token 和 dev 模式下的 X-User-ID
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  const userId = localStorage.getItem("user_id")
  if (userId) {
    config.headers["X-User-ID"] = userId
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem("access_token")
      localStorage.removeItem("user_id")
    }
    return Promise.reject(error)
  },
)

export default api
