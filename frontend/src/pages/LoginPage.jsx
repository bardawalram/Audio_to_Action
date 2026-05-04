import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { MicrophoneIcon } from '@heroicons/react/24/solid'
import authService from '../services/authService'
import {
  loginStart,
  loginSuccess,
  loginFailure,
} from '../store/slices/authSlice'

const LoginPage = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { loading, error } = useSelector((state) => state.auth)
  const location = useLocation()
  const justRegistered = location.state?.registered

  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  })

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      dispatch(loginStart())

      const response = await authService.login(
        credentials.username,
        credentials.password
      )

      // Response now includes user data from backend
      dispatch(
        loginSuccess({
          access: response.access,
          refresh: response.refresh,
          user: response.user,
        })
      )

      // Role-based redirect
      const userRole = response.user?.role
      if (userRole === 'ACCOUNTANT') {
        navigate('/dashboard')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      console.error('Login error:', err)
      const errorMessage =
        err.response?.data?.detail || 'Invalid username or password'
      dispatch(loginFailure(errorMessage))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-blue-100 p-4 rounded-full">
              <MicrophoneIcon className="w-12 h-12 text-blue-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">ATOA</h1>
          <p className="text-gray-600 mt-2">Voice-Driven School ERP System</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Success Message after registration */}
          {justRegistered && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
              <p className="text-sm">Account created successfully! Please sign in.</p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Username */}
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your username"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Sign Up Link */}
        <p className="text-center text-sm text-gray-600 mt-6">
          Don't have an account?{' '}
          <Link to="/signup" className="text-blue-600 font-semibold hover:text-blue-700">
            Sign Up
          </Link>
        </p>

        {/* Demo Credentials */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 text-center mb-2">
            Demo Credentials:
          </p>
          <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 space-y-1">
            <p>
              <span className="font-semibold">Teacher:</span> teacher1 / password123
            </p>
            <p>
              <span className="font-semibold">Accountant:</span> accountant1 / password123
            </p>
            <p>
              <span className="font-semibold">Admin:</span> admin / admin123
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
