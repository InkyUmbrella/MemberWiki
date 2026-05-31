import axios from "axios"

const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("未登录，请先登录")
    }
    return Promise.reject(error)
  },
)

export default api
