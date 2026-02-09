import {useEffect, useRef, useState} from 'react'
import api from '../api/client'

export default function CityAutocomplete({value, onChange, onSelect, onClear, placeholder}) {
    const [query, setQuery] = useState(value || '')
    const [suggestions, setSuggestions] = useState([])
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [activeIndex, setActiveIndex] = useState(-1)
    const wrapperRef = useRef(null)
    const debounceRef = useRef(null)

    useEffect(() => {
        setQuery(value || '')
    }, [value])

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const fetchSuggestions = (q) => {
        clearTimeout(debounceRef.current)
        if (q.length < 2) {
            setSuggestions([])
            setOpen(false)
            return
        }
        debounceRef.current = setTimeout(async () => {
            setLoading(true)
            try {
                const {data} = await api.get('weather/cities/', {params: {q}})
                setSuggestions(data)
                setOpen(data.length > 0)
                setActiveIndex(-1)
            } catch {
                setSuggestions([])
            } finally {
                setLoading(false)
            }
        }, 300)
    }

    const formatLabel = (item) =>
        item.state
            ? `${item.name}, ${item.state}, ${item.country}`
            : `${item.name}, ${item.country}`

    const handleInput = (e) => {
        const val = e.target.value
        setQuery(val)
        onChange(val)
        onSelect?.(null)
        fetchSuggestions(val)
    }

    const handlePick = (item) => {
        const label = formatLabel(item)
        setQuery(label)
        onChange(label)
        onSelect?.(item)
        setOpen(false)
        setSuggestions([])
    }

    const handleClear = () => {
        setQuery('')
        onChange('')
        onSelect?.(null)
        onClear?.()
        setSuggestions([])
        setOpen(false)
    }

    const handleKeyDown = (e) => {
        if (!open) return
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setActiveIndex((i) => (i < suggestions.length - 1 ? i + 1 : 0))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setActiveIndex((i) => (i > 0 ? i - 1 : suggestions.length - 1))
        } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault()
            handlePick(suggestions[activeIndex])
        } else if (e.key === 'Escape') {
            setOpen(false)
        }
    }

    return (
        <div ref={wrapperRef} className="relative">
            <input
                type="text"
                value={query}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                onFocus={() => suggestions.length > 0 && setOpen(true)}
                placeholder={placeholder || 'Enter city name...'}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            {query && !loading && (
                <button
                    type="button"
                    onClick={handleClear}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            )}
            {loading && (
                <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-500"/>
                </div>
            )}
            {open && (
                <ul className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {suggestions.map((item, i) => (
                        <li
                            key={`${item.lat}-${item.lon}-${i}`}
                            onClick={() => handlePick(item)}
                            className={`px-3 py-2 text-sm cursor-pointer transition-colors ${
                                i === activeIndex ? 'bg-indigo-50' : 'hover:bg-gray-50'
                            }`}
                        >
                            <span className="font-medium text-gray-800">{item.name}</span>
                            <span className="text-gray-400 ml-1">
                {item.state ? `${item.state}, ` : ''}
                                {item.country}
              </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
