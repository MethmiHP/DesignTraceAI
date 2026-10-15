import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { readSavedTheme } from './components/api-component/useTheme'

// Apply the saved palette before the first React render.
document.documentElement.dataset.theme = readSavedTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
