import {useEffect, useState} from 'react'
import {useNavigate} from 'react-router-dom'
import {useAuth} from '../context/AuthContext'
import CityAutocomplete from './CityAutocomplete'

const NOTIFICATION_TYPES = [
    {value: 'email', label: 'Email'},
    {value: 'webhook', label: 'Webhook'},
]

const INTERVAL_OPTIONS = [1, 3, 6, 12]

export default function SubscriptionForm({onSubmit, initial, onCancel}) {
    const [city, setCity] = useState('')
    const [intervalHours, setIntervalHours] = useState(6)
    const [notificationType, setNotificationType] = useState('email')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState('')
    const {user} = useAuth()
    const navigate = useNavigate()

    useEffect(() => {
        if (initial) {
            setCity(initial.city?.name || '')
            setIntervalHours(initial.interval_hours)
            setNotificationType(initial.notification_type)
        }
    }, [initial])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        if (!city.trim()) {
            setError('City is required.')
            return
        }
        if (notificationType === 'webhook' && !user?.webhook_url) {
            navigate('/profile', {state: {reason: 'webhook'}})
            return
        }
        setSubmitting(true)
        try {
            await onSubmit({
                city: {name: city},
                interval_hours: intervalHours,
                notification_type: notificationType,
            })
            if (!initial) {
                setCity('')
                setIntervalHours(6)
                setNotificationType('email')
            }
        } catch (err) {
            const data = err.response?.data
            if (data) {
                const messages = Object.values(data).flat().join(' ')
                setError(messages || 'Failed to save subscription.')
            } else {
                setError('Failed to save subscription.')
            }
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-md p-4 sm:p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
                {initial ? 'Edit Subscription' : 'New Subscription'}
            </h3>
            {error && (
                <div className="mb-4 bg-red-50 text-red-700 text-sm p-3 rounded-lg">{error}</div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                    <CityAutocomplete
                        value={city}
                        onChange={setCity}
                        placeholder="e.g. London"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Interval</label>
                    <select
                        value={intervalHours}
                        onChange={(e) => setIntervalHours(Number(e.target.value))}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                        {INTERVAL_OPTIONS.map((h) => (
                            <option key={h} value={h}>
                                Every {h}h
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Notify via</label>
                    <select
                        value={notificationType}
                        onChange={(e) => setNotificationType(e.target.value)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                        {NOTIFICATION_TYPES.map((t) => (
                            <option key={t.value} value={t.value}>
                                {t.label}
                            </option>
                        ))}
                    </select>
                    {notificationType === 'webhook' && !user?.webhook_url && (
                        <p className="mt-1 text-xs text-amber-600">
                            Webhook URL not set — you'll be redirected to profile.
                        </p>
                    )}
                </div>
                <div className="flex items-end gap-2">
                    <button
                        type="submit"
                        disabled={submitting}
                        className="flex-1 bg-indigo-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                    >
                        {submitting ? 'Saving...' : initial ? 'Update' : 'Add'}
                    </button>
                    {onCancel && (
                        <button
                            type="button"
                            onClick={onCancel}
                            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                    )}
                </div>
            </div>
        </form>
    )
}
