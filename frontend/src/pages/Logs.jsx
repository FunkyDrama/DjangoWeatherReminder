import {useEffect, useState} from 'react'
import api from '../api/client'

export default function Logs() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api
            .get('notifications/logs/')
            .then((res) => setLogs(res.data.results || res.data))
            .catch(() => {
            })
            .finally(() => setLoading(false))
    }, [])

    if (loading) {
        return (
            <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"/>
            </div>
        )
    }

    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Notification Logs</h2>
            {!logs.length ? (
                <div className="bg-white rounded-xl shadow-md p-6 text-center text-gray-500">
                    No notifications sent yet.
                </div>
            ) : (
                <>
                    <div className="hidden sm:block bg-white rounded-xl shadow-md overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-left text-gray-600">
                            <tr>
                                <th className="px-6 py-3 font-medium">City</th>
                                <th className="px-6 py-3 font-medium">Type</th>
                                <th className="px-6 py-3 font-medium">Status</th>
                                <th className="px-6 py-3 font-medium">Sent At</th>
                                <th className="px-6 py-3 font-medium">Response</th>
                            </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                            {logs.map((log) => (
                                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-800">{log.city}</td>
                                    <td className="px-6 py-4">
                      <span
                          className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-1 rounded-full">
                        {log.notification_type}
                      </span>
                                    </td>
                                    <td className="px-6 py-4">
                      <span
                          className={`inline-block text-xs font-medium px-2 py-1 rounded-full ${
                              log.status === 'success'
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-red-100 text-red-700'
                          }`}
                      >
                        {log.status}
                      </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-500">
                                        {new Date(log.sent_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-gray-500 max-w-xs truncate">
                                        {log.response || '-'}
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="sm:hidden space-y-3">
                        {logs.map((log) => (
                            <div key={log.id} className="bg-white rounded-xl shadow-md p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-medium text-gray-800">{log.city}</h4>
                                    <span
                                        className={`text-xs font-medium px-2 py-1 rounded-full ${
                                            log.status === 'success'
                                                ? 'bg-green-100 text-green-700'
                                                : 'bg-red-100 text-red-700'
                                        }`}
                                    >
                    {log.status}
                  </span>
                                </div>
                                <div className="text-sm text-gray-500 space-y-1">
                                    <div className="flex items-center gap-2">
                    <span
                        className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-0.5 rounded-full">
                      {log.notification_type}
                    </span>
                                        <span>{new Date(log.sent_at).toLocaleString()}</span>
                                    </div>
                                    {log.response && (
                                        <p className="text-gray-400 truncate">{log.response}</p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    )
}
