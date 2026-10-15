import { useEffect, useState } from 'react'

const storageKey = 'designtrace-theme'

export function readSavedTheme() {
  try {
    return window.localStorage.getItem(storageKey) === 'light' ? 'light' : 'dark'
  } catch {
    return 'dark'
  }
}

export default function useTheme() {
  const [theme, setTheme] = useState(readSavedTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      window.localStorage.setItem(storageKey, theme)
    } catch {
      // Theme switching still works when browser storage is unavailable.
    }
  }, [theme])

  return {
    theme,
    toggleTheme: () => setTheme((current) => current === 'dark' ? 'light' : 'dark'),
  }
}
