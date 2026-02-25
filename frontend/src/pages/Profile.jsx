import {useState} from 'react'
import {useLocation} from 'react-router-dom'
import {useAuth} from '../context/AuthContext'
import api from '../api/client'

export default function Profile() {
    const {user, updateUser} = useAuth()
    const location = useLocation()
    const fromWebhook = location.state?.reason === 'webhook'

    const [webhookUrl, setWebhookUrl] = useState(user?.webhook_url || '')
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState(
        fromWebhook ? 'Please set your Webhook URL before creating a webhook subscription.' : '',
    )

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSaving(true)
        setMessage('')
        try {
            const {data} = await api.patch('auth/me/', {webhook_url: webhookUrl || null})
            updateUser(data)
            setMessage('Profile updated successfully.')
        } catch {
            setMessage('Failed to update profile.')
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="max-w-lg">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Profile</h2>
            <div className="bg-white rounded-xl shadow-md p-4 sm:p-6 space-y-5">
                {fromWebhook && (
                    <div className="bg-amber-50 text-amber-700 text-sm p-3 rounded-lg">
                        You need to set a Webhook URL to use webhook notifications.
                    </div>
                )}
                <div>
                    <label className="block text-sm font-medium text-gray-500 mb-1">Email</label>
                    <p className="text-gray-800 font-medium">{user?.email}</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
                        <div className="relative">
                            <input
                                type="url"
                                value={webhookUrl}
                                onChange={(e) => setWebhookUrl(e.target.value)}
                                placeholder="https://example.com/webhook"
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                            />
                            {webhookUrl && (
                                <button
                                    type="button"
                                    onClick={() => setWebhookUrl('')}
                                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                         strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
                                    </svg>
                                </button>
                            )}
                        </div>
                        <p className="mt-1 text-xs text-gray-400">
                            Weather notifications will be sent to this URL if subscription type is webhook.
                        </p>
                    </div>
                    {message && (
                        <div
                            className={`text-sm p-3 rounded-lg ${
                                message.includes('success')
                                    ? 'bg-green-50 text-green-700'
                                    : message.includes('Failed')
                                        ? 'bg-red-50 text-red-700'
                                        : 'bg-amber-50 text-amber-700'
                            }`}
                        >
                            {message}
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={saving}
                        className="bg-indigo-600 text-white rounded-lg px-6 py-2 font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                    >
                        {saving ? 'Saving...' : 'Save'}
                    </button>
                </form>
            </div>
        </div>
    )
}
