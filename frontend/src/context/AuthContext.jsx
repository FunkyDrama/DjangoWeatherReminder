import {createContext, useContext, useEffect, useState} from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({children}) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('access')
        if (token) {
            api
                .get('auth/me/')
                .then((res) => setUser(res.data))
                .catch(() => {
                    localStorage.removeItem('access')
                    localStorage.removeItem('refresh')
                })
                .finally(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [])

    const login = async (email, password) => {
        const {data} = await api.post('auth/login/', {email, password})
        localStorage.setItem('access', data.access)
        localStorage.setItem('refresh', data.refresh)
        const me = await api.get('auth/me/')
        setUser(me.data)
    }

    const register = async (username, email, password) => {
        await api.post('auth/register/', {username, email, password})
        await login(email, password)
    }

    const logout = () => {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        setUser(null)
    }

    const updateUser = (data) => setUser(data)

    return (
        <AuthContext.Provider value={{user, loading, login, register, logout, updateUser}}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => useContext(AuthContext)
