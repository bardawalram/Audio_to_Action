import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  ArrowRightOnRectangleIcon,
  ClipboardDocumentCheckIcon,
  AcademicCapIcon,
  MicrophoneIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { logout } from '../store/slices/authSlice'
import VoiceRecorder from '../components/voice/VoiceRecorder'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import Notification from '../components/common/Notification'

const DashboardPage = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { user } = useSelector((state) => state.auth)

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  const navigationCards = [
    {
      title: 'Attendance Management',
      description: 'View and mark attendance for all classes',
      icon: ClipboardDocumentCheckIcon,
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
      path: '/attendance'
    },
    {
      title: 'Marks Management',
      description: 'View and update student marks',
      icon: AcademicCapIcon,
      color: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-600',
      path: '/marks'
    },
    {
      title: 'Voice Commands',
      description: 'Use voice to enter data quickly',
      icon: MicrophoneIcon,
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-600',
      path: '#voice',
      isAnchor: true
    },
    {
      title: 'Reports & Analytics',
      description: 'View student performance reports',
      icon: ChartBarIcon,
      color: 'bg-orange-500',
      hoverColor: 'hover:bg-orange-600',
      path: '/reports'
    }
  ]

  const handleCardClick = (card) => {
    if (card.isAnchor) {
      document.getElementById('voice-section')?.scrollIntoView({ behavior: 'smooth' })
    } else {
      navigate(card.path)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">ReATOA</h1>
              <p className="text-sm text-gray-600">Voice-Driven School ERP System</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800">
                  {user?.username || 'User'}
                </p>
                <p className="text-xs text-gray-500">Teacher</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors shadow-md"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            Welcome, {user?.username || 'Teacher'}!
          </h2>
          <p className="text-gray-600 text-lg">
            Manage your classes efficiently with our voice-driven system
          </p>
        </div>

        {/* Navigation Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {navigationCards.map((card, index) => {
            const Icon = card.icon
            return (
              <button
                key={index}
                onClick={() => handleCardClick(card)}
                className={`${card.color} ${card.hoverColor} text-white rounded-xl shadow-lg p-6 transition-all duration-300 hover:scale-105 hover:shadow-xl text-left`}
              >
                <div className="flex flex-col items-start space-y-4">
                  <div className="bg-white bg-opacity-20 p-3 rounded-lg">
                    <Icon className="w-8 h-8" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold mb-2">{card.title}</h3>
                    <p className="text-sm opacity-90">{card.description}</p>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Voice Command Section */}
        <div id="voice-section" className="scroll-mt-8">
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <MicrophoneIcon className="w-7 h-7 mr-3 text-blue-600" />
              Voice Command Center
            </h2>
            <p className="text-gray-600 mb-4">
              Use your voice to enter marks, mark attendance, and view student details.
              Simply click the microphone button and speak your command.
            </p>
          </div>

          {/* Voice Recorder */}
          <VoiceRecorder />
        </div>

        {/* Confirmation Dialog */}
        <ConfirmationDialog />

        {/* Notification */}
        <Notification />
      </div>
    </div>
  )
}

export default DashboardPage
