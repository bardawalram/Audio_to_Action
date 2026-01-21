import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { hideNotification } from '../../store/slices/uiSlice'

const Notification = () => {
  const dispatch = useDispatch()
  const { notification } = useSelector((state) => state.ui)

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        dispatch(hideNotification())
      }, 5000) // Auto-hide after 5 seconds

      return () => clearTimeout(timer)
    }
  }, [notification, dispatch])

  if (!notification) return null

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircleIcon className="w-6 h-6 text-green-600" />
      case 'error':
        return <XCircleIcon className="w-6 h-6 text-red-600" />
      case 'warning':
        return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600" />
      case 'info':
      default:
        return <InformationCircleIcon className="w-6 h-6 text-blue-600" />
    }
  }

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  const getTextColor = () => {
    switch (notification.type) {
      case 'success':
        return 'text-green-800'
      case 'error':
        return 'text-red-800'
      case 'warning':
        return 'text-yellow-800'
      case 'info':
      default:
        return 'text-blue-800'
    }
  }

  // CRITICAL FIX: Safely extract string message from any object
  const getMessageString = (message) => {
    // If already a string, return it
    if (typeof message === 'string') {
      return message
    }

    // If it's an object, try to extract meaningful text
    if (typeof message === 'object' && message !== null) {
      // Try common message fields
      if (message.message) return String(message.message)
      if (message.error) return String(message.error)
      if (message.text) return String(message.text)
      if (message.detail) return String(message.detail)

      // If it's an error object with audio_file key (validation error)
      if (message.audio_file) {
        return Array.isArray(message.audio_file)
          ? message.audio_file.join(', ')
          : String(message.audio_file)
      }

      // Last resort: stringify the object
      try {
        return JSON.stringify(message)
      } catch (e) {
        return 'Unknown error'
      }
    }

    // Fallback for other types
    return String(message)
  }

  const safeMessage = getMessageString(notification.message)

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div
        className={`
          flex items-center space-x-3 px-4 py-3 rounded-lg shadow-lg border
          ${getBackgroundColor()}
          max-w-md
        `}
      >
        {getIcon()}
        <p className={`flex-1 text-sm font-medium ${getTextColor()}`}>
          {safeMessage}
        </p>
        <button
          onClick={() => dispatch(hideNotification())}
          className="text-gray-400 hover:text-gray-600"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}

export default Notification
