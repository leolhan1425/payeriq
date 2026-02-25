import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import PracticeSetup from './pages/PracticeSetup'
import ContractUpload from './pages/ContractUpload'
import RateReview from './pages/RateReview'
import Report from './pages/Report'
import Landing from './pages/Landing'
import Layout from './components/Layout'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>
  return user ? children : <Navigate to="/login" />
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/practice" element={<PracticeSetup />} />
            <Route path="/contracts/new/upload" element={<ContractUpload />} />
            <Route path="/contracts/:id/review" element={<RateReview />} />
            <Route path="/contracts/:id/report" element={<Report />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
