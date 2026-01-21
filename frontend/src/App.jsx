import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AttendanceListPage from './pages/AttendanceListPage'
import AttendanceSheetPage from './pages/AttendanceSheetPage'
import MarksListPage from './pages/MarksListPage'
import MarksSheetPage from './pages/MarksSheetPage'
import QuestionWisePage from './pages/QuestionWisePage'
import ProtectedRoute from './components/common/ProtectedRoute'

function App() {
  const { isAuthenticated } = useSelector((state) => state.auth)

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
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
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
