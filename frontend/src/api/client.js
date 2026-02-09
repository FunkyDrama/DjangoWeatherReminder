import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1/',
})

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config
        if (error.response?.status === 401 && !original._retry) {
            original._retry = true
            const refresh = localStorage.getItem('refresh')
            if (refresh) {
                try {
                    const {data} = await axios.post('/api/v1/auth/token/refresh/', {refresh})
                    localStorage.setItem('access', data.access)
                    original.headers.Authorization = `Bearer ${data.access}`
                    return api(original)
                } catch {
                    localStorage.removeItem('access')
                    localStorage.removeItem('refresh')
                    window.location.href = '/login'
                }
            }
        }
        return Promise.reject(error)
    },
)

export default api
