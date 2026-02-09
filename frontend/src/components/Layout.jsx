import {useState} from 'react'
import {Link, Outlet, useNavigate} from 'react-router-dom'
import {useAuth} from '../context/AuthContext'

export default function Layout() {
    const {user, logout} = useAuth()
    const navigate = useNavigate()
    const [menuOpen, setMenuOpen] = useState(false)

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    const closeMenu = () => setMenuOpen(false)

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="bg-white shadow">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <Link to="/" className="text-xl font-bold text-indigo-600">
                                Weather Reminder
                            </Link>
                            {user && (
                                <div className="hidden sm:flex items-center space-x-6 ml-8">
                                    <Link to="/" className="text-gray-600 hover:text-indigo-600 transition-colors">
                                        Dashboard
                                    </Link>
                                    <Link to="/logs" className="text-gray-600 hover:text-indigo-600 transition-colors">
                                        Logs
                                    </Link>
                                    <Link to="/profile"
                                          className="text-gray-600 hover:text-indigo-600 transition-colors">
                                        Profile
                                    </Link>
                                </div>
                            )}
                        </div>
                        {user && (
                            <>
                                <div className="hidden sm:flex items-center space-x-4">
                                    <span className="text-sm text-gray-500">{user.username}</span>
                                    <button
                                        onClick={handleLogout}
                                        className="text-sm text-red-600 hover:text-red-800 transition-colors"
                                    >
                                        Logout
                                    </button>
                                </div>
                                <div className="flex items-center sm:hidden">
                                    <button
                                        onClick={() => setMenuOpen((v) => !v)}
                                        className="p-2 rounded-md text-gray-600 hover:text-indigo-600 hover:bg-gray-100 transition-colors"
                                    >
                                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            {menuOpen ? (
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                      d="M6 18L18 6M6 6l12 12"/>
                                            ) : (
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                      d="M4 6h16M4 12h16M4 18h16"/>
                                            )}
                                        </svg>
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {user && menuOpen && (
                    <div className="sm:hidden border-t border-gray-100">
                        <div className="px-4 py-3 space-y-2">
                            <Link onClick={closeMenu} to="/"
                                  className="block py-2 text-gray-600 hover:text-indigo-600 transition-colors">
                                Dashboard
                            </Link>
                            <Link onClick={closeMenu} to="/logs"
                                  className="block py-2 text-gray-600 hover:text-indigo-600 transition-colors">
                                Logs
                            </Link>
                            <Link onClick={closeMenu} to="/profile"
                                  className="block py-2 text-gray-600 hover:text-indigo-600 transition-colors">
                                Profile
                            </Link>
                            <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
                                <span className="text-sm text-gray-500">{user.username}</span>
                                <button
                                    onClick={() => {
                                        closeMenu();
                                        handleLogout()
                                    }}
                                    className="text-sm text-red-600 hover:text-red-800 transition-colors"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </nav>
            <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
                <Outlet/>
            </main>
        </div>
    )
}
