import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { useState, useEffect } from 'react'
import {
  ArrowRightOnRectangleIcon,
  ClipboardDocumentCheckIcon,
  AcademicCapIcon,
  MicrophoneIcon,
  ChartBarIcon,
  ArrowRightIcon,
  UserCircleIcon,
  CalendarDaysIcon,
  UsersIcon,
  CheckBadgeIcon,
} from '@heroicons/react/24/outline'
import { logout } from '../store/slices/authSlice'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'
import Notification from '../components/common/Notification'

const DashboardPage = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { user } = useSelector((state) => state.auth)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [showProfile, setShowProfile] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  const greeting = () => {
    const hour = currentTime.getHours()
    if (hour < 12) return 'Good Morning'
    if (hour < 17) return 'Good Afternoon'
    return 'Good Evening'
  }

  const today = currentTime.toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  const stats = [
    { label: 'Total Classes', value: '10', icon: UsersIcon, color: '#3b82f6' },
    { label: 'Sections', value: '30', icon: CalendarDaysIcon, color: '#8b5cf6' },
    { label: 'Students', value: '600', icon: UserCircleIcon, color: '#06b6d4' },
    { label: 'Exams Done', value: '3', icon: CheckBadgeIcon, color: '#f59e0b' },
  ]

  const modules = [
    {
      title: 'Attendance Management',
      desc: 'View and mark attendance for all classes',
      icon: ClipboardDocumentCheckIcon,
      path: '/attendance',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    },
    {
      title: 'Marks Management',
      desc: 'View and update student marks',
      icon: AcademicCapIcon,
      path: '/marks',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    },
    {
      title: 'Voice Commands',
      desc: 'Use voice to enter data quickly',
      icon: MicrophoneIcon,
      path: null,
      gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
      isVoice: true,
    },
    {
      title: 'Reports & Analytics',
      desc: 'View student performance reports',
      icon: ChartBarIcon,
      path: '/reports',
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    },
  ]

  const voiceExamples = [
    '"Update marks for student 3, maths 95, hindi 88"',
    '"Mark all present except student 5 and 8"',
    '"Open class 4th section B"',
    '"Download progress report for roll 12"',
  ]

  return (
    <div className="min-h-screen bg-[#f8fafc]">

      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-100">
        <div className="max-w-full mx-auto px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center shadow-md"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}
            >
              <MicrophoneIcon className="w-4 h-4 text-white" />
            </div>
            <div className="leading-tight">
              <h1 className="text-base font-extrabold text-gray-900 tracking-tight">ATOA</h1>
              <p className="text-[9px] text-gray-400 font-semibold uppercase tracking-[0.12em]">Audio to Action</p>
            </div>
          </div>
          <div className="relative">
            <button
              onClick={() => setShowProfile(!showProfile)}
              className="flex items-center gap-2.5 bg-gray-50 hover:bg-gray-100 rounded-full pl-1.5 pr-4 py-1.5 transition-all"
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-md"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}
              >
                {(user?.username || 'T')[0].toUpperCase()}
              </div>
              <div className="leading-tight text-left">
                <p className="text-sm font-semibold text-gray-800">{user?.username || 'User'}</p>
                <p className="text-[10px] text-gray-400 font-medium">{user?.role || 'Teacher'}</p>
              </div>
            </button>

            {/* Profile Dropdown */}
            {showProfile && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowProfile(false)} />
                <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden">
                  {/* Profile Header */}
                  <div className="px-5 pt-5 pb-4 text-center" style={{ background: 'linear-gradient(135deg, #4f46e520, #7c3aed20)' }}>
                    <div
                      className="w-14 h-14 rounded-full flex items-center justify-center text-lg font-bold text-white mx-auto shadow-lg"
                      style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}
                    >
                      {(user?.username || 'T')[0].toUpperCase()}
                    </div>
                    <p className="mt-2.5 text-base font-bold text-gray-900">{user?.username || 'User'}</p>
                    <p className="text-xs text-gray-500">{user?.email || `${user?.username || 'user'}@school.edu`}</p>
                    <span className="inline-block mt-2 text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                      {user?.role || 'Teacher'}
                    </span>
                  </div>
                  {/* Divider */}
                  <div className="border-t border-gray-100" />
                  {/* Actions */}
                  <div className="p-2">
                    <button
                      onClick={() => {
                        setShowProfile(false)
                        handleLogout()
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                    >
                      <ArrowRightOnRectangleIcon className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </nav>

      <div className="max-w-full mx-auto px-8 pt-5 pb-12">

        {/* Hero — compact */}
        <div
          className="relative rounded-2xl overflow-hidden mb-5"
          style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a78bfa 100%)' }}
        >
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
          <div className="absolute top-[-40px] right-[-30px] w-[140px] h-[140px] rounded-full bg-white/10" />
          <div className="absolute bottom-[-20px] left-[8%] w-[90px] h-[90px] rounded-full bg-white/10" />

          <div className="relative z-10 px-7 py-7 flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-white/80 text-xs font-medium mb-0.5">{today}</p>
              <h2 className="text-2xl font-extrabold text-white leading-tight tracking-tight drop-shadow-sm">
                {greeting()}, {user?.username || 'Teacher'}!
              </h2>
              <p className="text-white/90 mt-1 text-sm max-w-md">
                Manage your classes effortlessly. Use voice commands or navigate directly.
              </p>
            </div>
            <button
              onClick={() => document.getElementById('voice-section')?.scrollIntoView({ behavior: 'smooth' })}
              className="flex items-center gap-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white font-semibold text-xs px-8 py-2.5 rounded-xl transition-all border border-white/20 hover:border-white/40 shadow-lg flex-shrink-0"
            >
              <MicrophoneIcon className="w-4 h-4" />
              Try Voice Command
            </button>
          </div>
        </div>

        {/* Stats Row — compact */}
        <div className="grid grid-cols-4 gap-3 mb-5">
          {stats.map((stat, i) => {
            const Icon = stat.icon
            return (
              <div key={i} className="bg-white rounded-xl px-4 py-3.5 border border-gray-100 hover:shadow-md transition-all duration-200">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${stat.color}12` }}>
                    <Icon className="w-3.5 h-3.5" style={{ color: stat.color }} />
                  </div>
                  <p className="text-[11px] text-gray-400 font-medium">{stat.label}</p>
                </div>
                <p className="text-xl font-extrabold text-gray-900 pl-0.5">{stat.value}</p>
              </div>
            )
          })}
        </div>

        {/* Module Cards — compact */}
        <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-3">Quick Access</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {modules.map((mod, i) => {
            const Icon = mod.icon
            return (
              <button
                key={i}
                onClick={() => {
                  if (mod.isVoice) {
                    document.getElementById('voice-section')?.scrollIntoView({ behavior: 'smooth' })
                  } else {
                    navigate(mod.path)
                  }
                }}
                className="group relative text-left rounded-xl overflow-hidden transition-all duration-300 hover:scale-[1.03] hover:shadow-xl"
              >
                <div className="absolute inset-0" style={{ background: mod.gradient }} />
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="absolute -bottom-3 -right-3 opacity-10">
                  <Icon className="w-24 h-24 text-white" />
                </div>

                <div className="relative z-10 p-5 min-h-[130px] flex flex-col justify-between">
                  <div className="w-9 h-9 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="mt-4">
                    <h4 className="text-[13px] font-bold text-white mb-0.5">{mod.title}</h4>
                    <p className="text-[11px] text-white/80 leading-relaxed">{mod.desc}</p>
                  </div>
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <ArrowRightIcon className="w-3.5 h-3.5 text-white" />
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Voice Commands — compact */}
        <div id="voice-section" className="scroll-mt-16">
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center gap-2.5 mb-4">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shadow-md"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}
              >
                <MicrophoneIcon className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-gray-900">Voice Command Center</h3>
                <p className="text-[10px] text-gray-400">Click the mic and try saying these</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {voiceExamples.map((cmd, i) => (
                <div
                  key={i}
                  className="group flex items-center gap-2.5 bg-gray-50 hover:bg-indigo-50 rounded-lg px-4 py-2.5 transition-all duration-200 cursor-default border border-transparent hover:border-indigo-100"
                >
                  <div className="w-5 h-5 rounded-full bg-gray-200 group-hover:bg-indigo-200 flex items-center justify-center flex-shrink-0 transition-colors">
                    <MicrophoneIcon className="w-2.5 h-2.5 text-gray-500 group-hover:text-indigo-600 transition-colors" />
                  </div>
                  <p className="text-xs text-gray-500 group-hover:text-indigo-700 font-medium transition-colors">
                    {cmd}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      <FloatingVoiceButton />
      <ConfirmationDialog />
      <VoiceReceiptModal />
      <Notification />
    </div>
  )
}

export default DashboardPage
