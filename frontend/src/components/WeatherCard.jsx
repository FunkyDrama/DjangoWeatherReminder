export default function WeatherCard({data}) {
    if (!data) return null

    const iconUrl = data.icon
        ? `https://openweathermap.org/img/wn/${data.icon}@2x.png`
        : null

    return (
        <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-2xl font-bold text-gray-800">{data.city}</h3>
                    <p className="text-gray-500 capitalize">{data.description}</p>
                </div>
                {iconUrl && <img src={iconUrl} alt={data.description} className="w-16 h-16"/>}
            </div>
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div className="bg-indigo-50 rounded-lg p-3">
                    <p className="text-gray-500">Temperature</p>
                    <p className="text-lg font-semibold text-indigo-700">{data.temperature}°C</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-gray-500">Feels Like</p>
                    <p className="text-lg font-semibold text-blue-700">{data.feels_like}°C</p>
                </div>
                <div className="bg-teal-50 rounded-lg p-3">
                    <p className="text-gray-500">Humidity</p>
                    <p className="text-lg font-semibold text-teal-700">{data.humidity}%</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-3">
                    <p className="text-gray-500">Wind</p>
                    <p className="text-lg font-semibold text-purple-700">{data.wind_speed} m/s</p>
                </div>
            </div>
        </div>
    )
}
