import {BrowserRouter, Route, Routes} from 'react-router-dom'
import {AuthProvider} from './context/AuthContext'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Logs from './pages/Logs'
import Profile from './pages/Profile'

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<Login/>}/>
                    <Route path="/register" element={<Register/>}/>
                    <Route
                        element={
                            <PrivateRoute>
                                <Layout/>
                            </PrivateRoute>
                        }
                    >
                        <Route path="/" element={<Dashboard/>}/>
                        <Route path="/logs" element={<Logs/>}/>
                        <Route path="/profile" element={<Profile/>}/>
                    </Route>
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    )
}
