import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AppConsoleVersion } from '@penguintechinc/react-libs'
import Login from './components/Login'
import TestRunner from './components/TestRunner'
import { checkAuthStatus } from './services/api'
import './App.css'

interface User {
  id: number
  username: string
  email: string
  role: string
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [authEnabled, setAuthEnabled] = useState<boolean>(true)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      console.log('[App] Checking authentication status...')
      const response = await checkAuthStatus()
      console.log('[App] Auth status:', response)

      setAuthEnabled(response.auth_enabled)
      setIsAuthenticated(response.authenticated)

      if (response.user) {
        setUser(response.user)
      }
    } catch (error) {
      console.error('[App] Failed to check auth status:', error)
      setAuthEnabled(true)
      setIsAuthenticated(false)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = (userData: User) => {
    console.log('[App] User logged in:', userData.username)
    setUser(userData)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    console.log('[App] User logged out')
    setUser(null)
    setIsAuthenticated(false)
  }

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Loading WaddlePerf...</p>
      </div>
    )
  }

  return (
    <Router>
      <AppConsoleVersion appName="WaddlePerf" webuiVersion="1.0.0" apiStatusUrl="/health" />
      <div className="app">
        <Routes>
          <Route
            path="/login"
            element={
              authEnabled && !isAuthenticated ? (
                <Login onLogin={handleLogin} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route
            path="/"
            element={
              authEnabled && !isAuthenticated ? (
                <Navigate to="/login" replace />
              ) : (
                <TestRunner user={user} onLogout={handleLogout} authEnabled={authEnabled} />
              )
            }
          />
        </Routes>
      </div>
    </Router>
  )
}

export default App
