import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
// Both stylesheets participate in the cascade; preserve their order when adjusting shared styles.
import './styles/theme.css'
import './styles/ltimindtree.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
