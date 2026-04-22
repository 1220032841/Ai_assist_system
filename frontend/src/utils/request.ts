import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const service = axios.create({
    baseURL: apiBaseURL,
    // Grading may call LLM and exceed a few seconds.
    timeout: 60000,
})

// Request interceptor
service.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    (response) => {
        return response
    },
    (error) => {
        if (error.code === 'ECONNABORTED') {
            ElMessage.error('请求超时：评分生成较慢，请稍后重试或刷新结果页')
            return Promise.reject(error)
        }

        if (error.response) {
            const { status, data } = error.response
            const detail = data?.detail || ''
            const invalidCredentials = detail === 'Could not validate credentials'
            if (status === 401 || invalidCredentials) {
                if (invalidCredentials) {
                    ElMessage.error('登录态已失效，请重新登录')
                } else {
                    ElMessage.error('Session expired, please login again')
                }
                localStorage.removeItem('token')
                window.location.href = '/login'
            } else if (status === 403) {
                ElMessage.error(detail || '没有权限执行此操作')
            } else {
                ElMessage.error(data.detail || 'Error')
            }
        } else {
            ElMessage.error('Network Error')
        }
        return Promise.reject(error)
    }
)

export default service
