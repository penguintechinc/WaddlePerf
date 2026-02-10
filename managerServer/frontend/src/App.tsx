import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppConsoleVersion } from '@penguintechinc/react-libs';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Organizations from './pages/Organizations';
import Statistics from './pages/Statistics';
import Profile from './pages/Profile';
import Devices from './pages/Devices';
import './App.css';

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppConsoleVersion webuiVersion="4.0.0" apiStatusUrl="/health" />
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <div className="app-layout">
                    <Navbar />
                    <Dashboard />
                  </div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute>
                  <div className="app-layout">
                    <Navbar />
                    <Users />
                  </div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/organizations"
              element={
                <ProtectedRoute>
                  <div className="app-layout">
                    <Navbar />
                    <Organizations />
                  </div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/statistics"
              element={
                <ProtectedRoute>
                  <div className="app-layout">
                    <Navbar />
                    <Statistics />
                  </div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <div className="app-layout">
                    <Navbar />
                    <Profile />
                  </div>
                </ProtectedRoute>
              }
            />
            <Route
              path="/devices"
              element={
                <ProtectedRoute>
                  <div className="app-layout">
                    <Navbar />
                    <Devices />
                  </div>
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
