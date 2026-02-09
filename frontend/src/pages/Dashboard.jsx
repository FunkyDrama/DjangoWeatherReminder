import {useCallback, useEffect, useState} from 'react'
import api from '../api/client'
import CityAutocomplete from '../components/CityAutocomplete'
import WeatherCard from '../components/WeatherCard'
import SubscriptionForm from '../components/SubscriptionForm'
import SubscriptionList from '../components/SubscriptionList'

export default function Dashboard() {
    const [city, setCity] = useState('')
    const [weather, setWeather] = useState(null)
    const [weatherLoading, setWeatherLoading] = useState(false)
    const [weatherError, setWeatherError] = useState('')
    const [subscriptions, setSubscriptions] = useState([])
    const [editing, setEditing] = useState(null)

    const fetchSubscriptions = useCallback(async () => {
        try {
            const {data} = await api.get('subscriptions/')
            setSubscriptions(data.results || data)
        } catch {
        }
    }, [])

    useEffect(() => {
        fetchSubscriptions()
    }, [fetchSubscriptions])

    const fetchWeather = async (item) => {
        if (!item) return
        setWeatherLoading(true)
        setWeatherError('')
        setWeather(null)
        try {
            const {data} = await api.get('weather/', {
                params: {lat: item.lat, lon: item.lon},
            })
            setWeather(data)
        } catch (err) {
            setWeatherError(err.response?.data?.detail || 'Failed to fetch weather.')
        } finally {
            setWeatherLoading(false)
        }
    }

    const handleCitySelect = (item) => {
        if (item) fetchWeather(item)
    }

    const handleClear = () => {
        setWeather(null)
        setWeatherError('')
    }

    const handleCreate = async (payload) => {
        await api.post('subscriptions/', payload)
        await fetchSubscriptions()
    }

    const handleUpdate = async (payload) => {
        await api.put(`subscriptions/${editing.id}/`, payload)
        setEditing(null)
        await fetchSubscriptions()
    }

    const handleDelete = async (id) => {
        await api.delete(`subscriptions/${id}/`)
        await fetchSubscriptions()
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Weather Search</h2>
                <CityAutocomplete
                    value={city}
                    onChange={setCity}
                    onSelect={handleCitySelect}
                    onClear={handleClear}
                    placeholder="Enter city name..."
                />
                {weatherLoading && (
                    <div className="flex justify-center py-6">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"/>
                    </div>
                )}
                {weatherError && (
                    <div className="mt-3 bg-red-50 text-red-700 text-sm p-3 rounded-lg">
                        {weatherError}
                    </div>
                )}
            </div>

            {weather && <WeatherCard data={weather}/>}

            <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Subscriptions</h2>
                {editing ? (
                    <SubscriptionForm
                        initial={editing}
                        onSubmit={handleUpdate}
                        onCancel={() => setEditing(null)}
                    />
                ) : (
                    <SubscriptionForm onSubmit={handleCreate}/>
                )}
            </div>

            <SubscriptionList
                subscriptions={subscriptions}
                onEdit={setEditing}
                onDelete={handleDelete}
            />
        </div>
    )
}
