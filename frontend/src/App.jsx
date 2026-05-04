import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import { setUser, logout } from './store/slices/authSlice'
import authService from './services/authService'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import AccountantDashboardPage from './pages/AccountantDashboardPage'
import AttendanceListPage from './pages/AttendanceListPage'
import AttendanceSheetPage from './pages/AttendanceSheetPage'
import MarksListPage from './pages/MarksListPage'
import MarksSheetPage from './pages/MarksSheetPage'
import QuestionWisePage from './pages/QuestionWisePage'
import ReportsPage from './pages/ReportsPage'
import FeeListPage from './pages/FeeListPage'
import FeeCollectionPage from './pages/FeeCollectionPage'
import FeeReportsPage from './pages/FeeReportsPage'
import ProtectedRoute from './components/common/ProtectedRoute'

function RoleDashboard() {
  const { user } = useSelector((state) => state.auth)

  if (user?.role === 'ACCOUNTANT') {
    return <AccountantDashboardPage />
  }
  return <DashboardPage />
}

function App() {
  const dispatch = useDispatch()
  const { isAuthenticated, token, user } = useSelector((state) => state.auth)

  // Fetch user profile on startup if we have a token but no user
  useEffect(() => {
    if (isAuthenticated && token && !user) {
      authService.getCurrentUser()
        .then((data) => {
          dispatch(setUser(data))
        })
        .catch(() => {
          // Token is invalid, logout
          dispatch(logout())
        })
    }
  }, [isAuthenticated, token, user, dispatch])

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route
        path="/signup"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <SignupPage />}
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <RoleDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/attendance"
        element={
          <ProtectedRoute>
            <AttendanceListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/attendance/:classNum/:section"
        element={
          <ProtectedRoute>
            <AttendanceSheetPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/marks"
        element={
          <ProtectedRoute>
            <MarksListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/marks/:classNum/:section"
        element={
          <ProtectedRoute>
            <MarksSheetPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/marks/:classNum/:section/question/:rollNumber/:subjectId"
        element={
          <ProtectedRoute>
            <QuestionWisePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      {/* Fee Management Routes */}
      <Route
        path="/fees"
        element={
          <ProtectedRoute>
            <FeeListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/fees/:classNum/:section"
        element={
          <ProtectedRoute>
            <FeeCollectionPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/fee-reports"
        element={
          <ProtectedRoute>
            <FeeReportsPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
