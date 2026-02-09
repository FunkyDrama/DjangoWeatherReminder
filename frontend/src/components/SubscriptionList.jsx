export default function SubscriptionList({subscriptions, onEdit, onDelete}) {
    if (!subscriptions.length) {
        return (
            <div className="bg-white rounded-xl shadow-md p-6 text-center text-gray-500">
                No subscriptions yet. Add one above!
            </div>
        )
    }

    return (
        <>
            <div className="hidden sm:block bg-white rounded-xl shadow-md overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-left text-gray-600">
                    <tr>
                        <th className="px-6 py-3 font-medium">City</th>
                        <th className="px-6 py-3 font-medium">Interval</th>
                        <th className="px-6 py-3 font-medium">Notify via</th>
                        <th className="px-6 py-3 font-medium">Last Notified</th>
                        <th className="px-6 py-3 font-medium text-right">Actions</th>
                    </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                    {subscriptions.map((sub) => (
                        <tr key={sub.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 font-medium text-gray-800">{sub.city.name}</td>
                            <td className="px-6 py-4 text-gray-600">Every {sub.interval_hours}h</td>
                            <td className="px-6 py-4">
                  <span
                      className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-1 rounded-full">
                    {sub.notification_type}
                  </span>
                            </td>
                            <td className="px-6 py-4 text-gray-500">
                                {sub.last_notified
                                    ? new Date(sub.last_notified).toLocaleString()
                                    : 'Never'}
                            </td>
                            <td className="px-6 py-4 text-right space-x-2">
                                <button
                                    onClick={() => onEdit(sub)}
                                    className="text-indigo-600 hover:text-indigo-800 transition-colors"
                                >
                                    Edit
                                </button>
                                <button
                                    onClick={() => onDelete(sub.id)}
                                    className="text-red-600 hover:text-red-800 transition-colors"
                                >
                                    Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>

            <div className="sm:hidden space-y-3">
                {subscriptions.map((sub) => (
                    <div key={sub.id} className="bg-white rounded-xl shadow-md p-4">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-gray-800">{sub.city.name}</h4>
                            <span
                                className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-1 rounded-full">
                {sub.notification_type}
              </span>
                        </div>
                        <div className="text-sm text-gray-500 space-y-1">
                            <p>Every {sub.interval_hours}h</p>
                            <p>
                                Last notified:{' '}
                                {sub.last_notified
                                    ? new Date(sub.last_notified).toLocaleString()
                                    : 'Never'}
                            </p>
                        </div>
                        <div className="mt-3 flex gap-3 border-t border-gray-100 pt-3">
                            <button
                                onClick={() => onEdit(sub)}
                                className="text-sm text-indigo-600 hover:text-indigo-800 transition-colors"
                            >
                                Edit
                            </button>
                            <button
                                onClick={() => onDelete(sub.id)}
                                className="text-sm text-red-600 hover:text-red-800 transition-colors"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </>
    )
}
