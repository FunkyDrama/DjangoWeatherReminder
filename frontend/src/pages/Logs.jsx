import {useCallback, useEffect, useRef, useState} from 'react'
import api from '../api/client'

const PAGE_SIZE = 10

function StatusBadge({status}) {
    const sent = status === 'sent'
    return (
        <span
            className={`inline-block text-xs font-medium px-2 py-1 rounded-full ${
                sent ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
        >
            {sent ? '✓ Sent' : '✗ Failed'}
        </span>
    )
}

export default function Logs() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [loadingMore, setLoadingMore] = useState(false)
    const [hasMore, setHasMore] = useState(false)
    const offsetRef = useRef(0)
    const sentinelRef = useRef(null)

    const fetchPage = useCallback(async (offset, replace) => {
        try {
            const res = await api.get('notifications/logs/', {
                params: {limit: PAGE_SIZE, offset},
            })
            const data = res.data
            const results = data.results ?? data
            const total = data.count ?? results.length
            setLogs(prev => replace ? results : [...prev, ...results])
            offsetRef.current = offset + results.length
            setHasMore(offsetRef.current < total)
        } catch {
            // silently ignore; existing logs stay on screen
        }
    }, [])

    // Initial load
    useEffect(() => {
        setLoading(true)
        offsetRef.current = 0
        fetchPage(0, true).finally(() => setLoading(false))
    }, [fetchPage])

    // Intersection Observer for infinite scroll
    useEffect(() => {
        if (!sentinelRef.current) return
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && hasMore && !loadingMore) {
                    setLoadingMore(true)
                    fetchPage(offsetRef.current, false).finally(() =>
                        setLoadingMore(false)
                    )
                }
            },
            {rootMargin: '200px'},
        )
        observer.observe(sentinelRef.current)
        return () => observer.disconnect()
    }, [hasMore, loadingMore, fetchPage])

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
                    {/* Desktop table */}
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
                                        <span className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-1 rounded-full">
                                            {log.notification_type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <StatusBadge status={log.status}/>
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

                    {/* Mobile cards */}
                    <div className="sm:hidden space-y-3">
                        {logs.map((log) => (
                            <div key={log.id} className="bg-white rounded-xl shadow-md p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-medium text-gray-800">{log.city}</h4>
                                    <StatusBadge status={log.status}/>
                                </div>
                                <div className="text-sm text-gray-500 space-y-1">
                                    <div className="flex items-center gap-2">
                                        <span className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-0.5 rounded-full">
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

                    {/* Infinite scroll sentinel */}
                    <div ref={sentinelRef} className="flex justify-center py-4">
                        {loadingMore && (
                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"/>
                        )}
                    </div>
                </>
            )}
        </div>
    )
}
