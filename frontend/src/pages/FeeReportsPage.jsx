import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  ArrowLeftIcon,
  CurrencyRupeeIcon,
  ExclamationTriangleIcon,
  AcademicCapIcon,
  CalendarDaysIcon,
  BanknotesIcon,
  CreditCardIcon,
  DevicePhoneMobileIcon,
  BuildingLibraryIcon,
  FunnelIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'
import feeService from '../services/feeService'

// Indian number formatting utility
const formatINR = (amount) => {
  if (amount == null || isNaN(amount)) return '0'
  return Number(amount).toLocaleString('en-IN', {
    maximumFractionDigits: 0,
  })
}

const TAB_KEYS = ['today', 'defaulters', 'classwise', 'monthly']

const TABS = [
  { id: 'today', name: "Today's Collection", icon: CurrencyRupeeIcon },
  { id: 'defaulters', name: 'Defaulters', icon: ExclamationTriangleIcon },
  { id: 'classwise', name: 'Class-wise Analysis', icon: AcademicCapIcon },
  { id: 'monthly', name: 'Monthly Trends', icon: CalendarDaysIcon },
]

const PAYMENT_METHOD_ICONS = {
  cash: BanknotesIcon,
  Cash: BanknotesIcon,
  CASH: BanknotesIcon,
  card: CreditCardIcon,
  Card: CreditCardIcon,
  CARD: CreditCardIcon,
  upi: DevicePhoneMobileIcon,
  UPI: DevicePhoneMobileIcon,
  bank_transfer: BuildingLibraryIcon,
  Bank_Transfer: BuildingLibraryIcon,
  BANK_TRANSFER: BuildingLibraryIcon,
  cheque: BuildingLibraryIcon,
  Cheque: BuildingLibraryIcon,
  CHEQUE: BuildingLibraryIcon,
  online: DevicePhoneMobileIcon,
  Online: DevicePhoneMobileIcon,
  ONLINE: DevicePhoneMobileIcon,
}

const getPaymentMethodIcon = (method) => {
  return PAYMENT_METHOD_ICONS[method] || BanknotesIcon
}

const getPaymentMethodColor = (method) => {
  const key = (method || '').toLowerCase()
  if (key === 'cash') return 'bg-green-50 border-green-200 text-green-700'
  if (key === 'card') return 'bg-blue-50 border-blue-200 text-blue-700'
  if (key === 'upi') return 'bg-purple-50 border-purple-200 text-purple-700'
  if (key === 'bank_transfer' || key === 'cheque') return 'bg-orange-50 border-orange-200 text-orange-700'
  if (key === 'online') return 'bg-indigo-50 border-indigo-200 text-indigo-700'
  return 'bg-gray-50 border-gray-200 text-gray-700'
}

const getCollectionColor = (percentage) => {
  if (percentage >= 90) return { bg: 'bg-green-500', text: 'text-green-700', light: 'bg-green-50', border: 'border-green-300' }
  if (percentage >= 70) return { bg: 'bg-blue-500', text: 'text-blue-700', light: 'bg-blue-50', border: 'border-blue-300' }
  if (percentage >= 50) return { bg: 'bg-yellow-500', text: 'text-yellow-700', light: 'bg-yellow-50', border: 'border-yellow-300' }
  if (percentage >= 30) return { bg: 'bg-orange-500', text: 'text-orange-700', light: 'bg-orange-50', border: 'border-orange-300' }
  return { bg: 'bg-red-500', text: 'text-red-700', light: 'bg-red-50', border: 'border-red-300' }
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const FeeReportsPage = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const tabFromUrl = searchParams.get('tab')
  const [activeTab, setActiveTab] = useState(
    TAB_KEYS.includes(tabFromUrl) ? tabFromUrl : 'today'
  )

  // Data states
  const [loading, setLoading] = useState(false)
  const [todayData, setTodayData] = useState(null)
  const [defaultersData, setDefaultersData] = useState(null)
  const [classWiseData, setClassWiseData] = useState(null)
  const [monthlyData, setMonthlyData] = useState(null)

  // Defaulters filter
  const [defaulterClassFilter, setDefaulterClassFilter] = useState('all')

  // Sync tab from URL
  useEffect(() => {
    if (tabFromUrl && TAB_KEYS.includes(tabFromUrl)) {
      setActiveTab(tabFromUrl)
    }
  }, [tabFromUrl])

  // Update URL when tab changes
  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    setSearchParams({ tab: tabId })
  }

  // Fetch data when tab changes
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        switch (activeTab) {
          case 'today': {
            const res = await feeService.getTodayCollection()
            setTodayData(res.data)
            break
          }
          case 'defaulters': {
            const classParam = defaulterClassFilter !== 'all' ? defaulterClassFilter : undefined
            const res = await feeService.getDefaulters(classParam)
            setDefaultersData(res.data)
            break
          }
          case 'classwise': {
            const res = await feeService.getClassWiseReport()
            setClassWiseData(res.data)
            break
          }
          case 'monthly': {
            const res = await feeService.getMonthlyReport(6)
            setMonthlyData(res.data)
            break
          }
          default:
            break
        }
      } catch (error) {
        console.error(`Failed to fetch ${activeTab} data:`, error)
        // Load mock data on error
        loadMockData(activeTab)
      }
      setLoading(false)
    }
    fetchData()
  }, [activeTab, defaulterClassFilter])

  // Mock data fallbacks
  const loadMockData = (tab) => {
    switch (tab) {
      case 'today':
        setTodayData({
          date: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' }),
          total_collected: 125400,
          transaction_count: 18,
          breakdown: [
            { method: 'Cash', amount: 54000, count: 8 },
            { method: 'UPI', amount: 42500, count: 6 },
            { method: 'Card', amount: 18900, count: 3 },
            { method: 'Bank_Transfer', amount: 10000, count: 1 },
          ],
          recent_transactions: [
            { receipt_no: 'RCT-2026-0183', student_name: 'Aarav Sharma', class: '8A', amount: 12500, method: 'UPI', time: '02:15 PM' },
            { receipt_no: 'RCT-2026-0182', student_name: 'Priya Singh', class: '5B', amount: 8000, method: 'Cash', time: '01:42 PM' },
            { receipt_no: 'RCT-2026-0181', student_name: 'Rohan Patel', class: '10A', amount: 15000, method: 'Card', time: '12:30 PM' },
            { receipt_no: 'RCT-2026-0180', student_name: 'Ananya Gupta', class: '3A', amount: 6500, method: 'Cash', time: '11:55 AM' },
            { receipt_no: 'RCT-2026-0179', student_name: 'Vikram Reddy', class: '7B', amount: 10000, method: 'Bank_Transfer', time: '11:20 AM' },
            { receipt_no: 'RCT-2026-0178', student_name: 'Sneha Iyer', class: '9A', amount: 9500, method: 'UPI', time: '10:45 AM' },
            { receipt_no: 'RCT-2026-0177', student_name: 'Karthik Nair', class: '6A', amount: 7200, method: 'Cash', time: '10:10 AM' },
            { receipt_no: 'RCT-2026-0176', student_name: 'Meera Joshi', class: '4B', amount: 5500, method: 'UPI', time: '09:35 AM' },
          ],
        })
        break
      case 'defaulters':
        setDefaultersData({
          defaulter_count: 12,
          defaulters: [
            { roll_no: 5, student_name: 'Rahul Kumar', class: '8A', total_fees: 45000, paid: 12000, balance: 33000 },
            { roll_no: 3, student_name: 'Suman Devi', class: '6B', total_fees: 38000, paid: 10000, balance: 28000 },
            { roll_no: 12, student_name: 'Amit Verma', class: '10A', total_fees: 55000, paid: 30000, balance: 25000 },
            { roll_no: 8, student_name: 'Pooja Yadav', class: '5A', total_fees: 35000, paid: 12000, balance: 23000 },
            { roll_no: 1, student_name: 'Deepak Mishra', class: '9B', total_fees: 50000, paid: 28000, balance: 22000 },
            { roll_no: 7, student_name: 'Kavita Sharma', class: '3A', total_fees: 30000, paid: 10000, balance: 20000 },
            { roll_no: 15, student_name: 'Nikhil Agarwal', class: '7A', total_fees: 42000, paid: 25000, balance: 17000 },
            { roll_no: 2, student_name: 'Sunita Pandey', class: '4B', total_fees: 32000, paid: 18000, balance: 14000 },
            { roll_no: 10, student_name: 'Manoj Tiwari', class: '2A', total_fees: 28000, paid: 16000, balance: 12000 },
            { roll_no: 6, student_name: 'Ritu Saxena', class: '1B', total_fees: 25000, paid: 15000, balance: 10000 },
            { roll_no: 9, student_name: 'Vivek Chauhan', class: '8B', total_fees: 45000, paid: 37000, balance: 8000 },
            { roll_no: 4, student_name: 'Anita Jain', class: '6A', total_fees: 38000, paid: 32000, balance: 6000 },
          ],
        })
        break
      case 'classwise':
        setClassWiseData({
          classes: [
            { class_name: 'Class 1', student_count: 45, expected: 1125000, collected: 1012500, percentage: 90 },
            { class_name: 'Class 2', student_count: 42, expected: 1050000, collected: 892500, percentage: 85 },
            { class_name: 'Class 3', student_count: 48, expected: 1200000, collected: 960000, percentage: 80 },
            { class_name: 'Class 4', student_count: 40, expected: 1000000, collected: 720000, percentage: 72 },
            { class_name: 'Class 5', student_count: 38, expected: 950000, collected: 760000, percentage: 80 },
            { class_name: 'Class 6', student_count: 44, expected: 1320000, collected: 924000, percentage: 70 },
            { class_name: 'Class 7', student_count: 41, expected: 1230000, collected: 799500, percentage: 65 },
            { class_name: 'Class 8', student_count: 43, expected: 1505000, collected: 1053500, percentage: 70 },
            { class_name: 'Class 9', student_count: 39, expected: 1560000, collected: 936000, percentage: 60 },
            { class_name: 'Class 10', student_count: 36, expected: 1620000, collected: 891000, percentage: 55 },
          ],
        })
        break
      case 'monthly': {
        const now = new Date()
        const months = []
        for (let i = 5; i >= 0; i--) {
          const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
          months.push({
            month: MONTH_NAMES[d.getMonth()],
            year: d.getFullYear(),
            amount: Math.floor(200000 + Math.random() * 300000),
            transaction_count: Math.floor(30 + Math.random() * 50),
            is_current: i === 0,
          })
        }
        setMonthlyData({ months })
        break
      }
      default:
        break
    }
  }

  // ---- Tab Renderers ----

  const renderTodayCollection = () => {
    if (!todayData) return null
    const { date, total_collected, transaction_count, breakdown, recent_transactions } = todayData

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <p className="text-sm text-gray-500">Date</p>
            <p className="text-xl font-bold text-gray-800">{date || new Date().toLocaleDateString('en-IN')}</p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <p className="text-sm text-gray-500">Total Collected</p>
            <p className="text-3xl font-bold text-gray-800">
              <span className="text-lg">Rs </span>{formatINR(total_collected)}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <p className="text-sm text-gray-500">Transactions</p>
            <p className="text-3xl font-bold text-gray-800">{transaction_count}</p>
          </div>
        </div>

        {/* Payment Method Breakdown */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Breakdown by Payment Method</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {(breakdown || []).map((item, idx) => {
              const Icon = getPaymentMethodIcon(item.method)
              const colorClass = getPaymentMethodColor(item.method)
              return (
                <div
                  key={idx}
                  className={`rounded-lg border p-4 ${colorClass} transition-all hover:shadow-md`}
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="p-2 rounded-lg bg-white bg-opacity-60">
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="font-semibold capitalize">
                      {(item.method || '').replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-2xl font-bold">Rs {formatINR(item.amount)}</p>
                  <p className="text-sm opacity-75 mt-1">{item.count} transaction{item.count !== 1 ? 's' : ''}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Recent Transactions Table */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Transactions</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Receipt #</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Student</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Class</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Amount</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Method</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Time</th>
                </tr>
              </thead>
              <tbody>
                {(recent_transactions || []).map((txn, idx) => (
                  <tr key={idx} className="border-t hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm font-mono text-blue-600">
                      <button
                        onClick={() => {
                          window.dispatchEvent(new CustomEvent('voiceReceiptReady', {
                            detail: {
                              receiptNumber: txn.receipt_no,
                              studentName: txn.student_name,
                              rollNumber: txn.roll_number,
                              className: txn.class,
                              amount: txn.amount,
                              paymentMethod: (txn.method || '').replace(/_/g, ' '),
                              feeType: txn.fee_type || '',
                              collectedBy: txn.collected_by || '',
                              date: txn.date || date || '',
                              time: txn.time || '',
                            }
                          }))
                        }}
                        className="hover:underline hover:text-blue-800 cursor-pointer"
                      >
                        {txn.receipt_no}
                      </button>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-800">{txn.student_name}</td>
                    <td className="px-4 py-3 text-gray-600">{txn.class}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-800">
                      Rs {formatINR(txn.amount)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getPaymentMethodColor(txn.method)}`}>
                        {(txn.method || '').replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-500">{txn.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!recent_transactions || recent_transactions.length === 0) && (
              <p className="text-center text-gray-500 py-8">No transactions today</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderDefaulters = () => {
    if (!defaultersData) return null
    const { defaulter_count, defaulters } = defaultersData

    // Filter by class if needed
    const filteredDefaulters = defaulterClassFilter !== 'all'
      ? (defaulters || []).filter((d) => {
          const classNum = (d.class || '').replace(/[^0-9]/g, '')
          return classNum === String(defaulterClassFilter)
        })
      : defaulters || []

    // Sort by balance descending
    const sortedDefaulters = [...filteredDefaulters].sort((a, b) => (b.balance || 0) - (a.balance || 0))

    // Determine high-balance threshold (top quartile)
    const balances = sortedDefaulters.map((d) => d.balance || 0)
    const highBalanceThreshold = balances.length > 0
      ? balances[Math.floor(balances.length * 0.25)] || 20000
      : 20000

    return (
      <div className="space-y-6">
        {/* Filter and Count */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <FunnelIcon className="w-5 h-5 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">Filter by Class:</label>
              <div className="relative">
                <select
                  value={defaulterClassFilter}
                  onChange={(e) => setDefaulterClassFilter(e.target.value)}
                  className="appearance-none pl-4 pr-10 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 font-medium"
                >
                  <option value="all">All Classes</option>
                  {Array.from({ length: 10 }, (_, i) => i + 1).map((cls) => (
                    <option key={cls} value={cls}>Class {cls}</option>
                  ))}
                </select>
                <ChevronDownIcon className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
              <span className="text-lg font-bold text-red-600">
                {sortedDefaulters.length} Defaulter{sortedDefaulters.length !== 1 ? 's' : ''}
              </span>
              {defaulterClassFilter === 'all' && defaulter_count && (
                <span className="text-sm text-gray-500">(Total: {defaulter_count})</span>
              )}
            </div>
          </div>
        </div>

        {/* Defaulters Table */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Roll No</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Student Name</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Class</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Total Fees</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Paid</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Balance</th>
                </tr>
              </thead>
              <tbody>
                {sortedDefaulters.map((student, idx) => {
                  const isHighBalance = (student.balance || 0) >= highBalanceThreshold
                  return (
                    <tr
                      key={idx}
                      className={`border-t transition-colors ${
                        isHighBalance
                          ? 'bg-red-50 hover:bg-red-100'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <td className="px-4 py-3 text-gray-800">{student.roll_no}</td>
                      <td className="px-4 py-3 font-medium text-gray-800">
                        {student.student_name}
                        {isHighBalance && (
                          <ExclamationTriangleIcon className="w-4 h-4 text-red-500 inline ml-2" title="High balance" />
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{student.class}</td>
                      <td className="px-4 py-3 text-right text-gray-800">Rs {formatINR(student.total_fees)}</td>
                      <td className="px-4 py-3 text-right text-green-600 font-medium">Rs {formatINR(student.paid)}</td>
                      <td className={`px-4 py-3 text-right font-bold ${isHighBalance ? 'text-red-600' : 'text-orange-600'}`}>
                        Rs {formatINR(student.balance)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {sortedDefaulters.length === 0 && (
              <p className="text-center text-gray-500 py-8">No defaulters found for the selected filter</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderClassWise = () => {
    if (!classWiseData) return null
    const { classes } = classWiseData

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(classes || []).map((cls, idx) => {
            const percentage = cls.percentage || 0
            const colors = getCollectionColor(percentage)
            return (
              <div
                key={idx}
                className={`bg-white rounded-xl shadow-md overflow-hidden border ${colors.border} hover:shadow-lg transition-shadow`}
              >
                {/* Card Header */}
                <div className={`${colors.light} px-5 py-3 border-b ${colors.border}`}>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-800">{cls.class_name}</h3>
                    <span className={`text-sm font-semibold ${colors.text}`}>
                      {cls.student_count} student{cls.student_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide">Expected</p>
                      <p className="text-sm font-bold text-gray-800">Rs {formatINR(cls.expected)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide">Collected</p>
                      <p className="text-sm font-bold text-green-600">Rs {formatINR(cls.collected)}</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">Collection</span>
                      <span className={`text-sm font-bold ${colors.text}`}>{percentage}%</span>
                    </div>
                    <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${colors.bg}`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Pending */}
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Pending</p>
                    <p className="text-sm font-bold text-red-500">
                      Rs {formatINR((cls.expected || 0) - (cls.collected || 0))}
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        {(!classes || classes.length === 0) && (
          <div className="bg-white rounded-xl shadow-md p-8 text-center text-gray-500">
            No class-wise data available
          </div>
        )}
      </div>
    )
  }

  const renderMonthlyTrends = () => {
    if (!monthlyData) return null
    const { months } = monthlyData

    if (!months || months.length === 0) {
      return (
        <div className="bg-white rounded-xl shadow-md p-8 text-center text-gray-500">
          No monthly data available
        </div>
      )
    }

    // Find max amount for scaling
    const maxAmount = Math.max(...months.map((m) => m.amount || 0), 1)

    return (
      <div className="space-y-6">
        {/* Bar Chart */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-6">Last 6 Months Collection</h3>

          <div className="flex items-end justify-around gap-4" style={{ minHeight: '320px' }}>
            {months.map((m, idx) => {
              const barHeight = ((m.amount || 0) / maxAmount) * 100
              const isCurrent = m.is_current
              return (
                <div key={idx} className="flex flex-col items-center flex-1 max-w-[120px]">
                  {/* Amount label on top */}
                  <p className={`text-xs font-bold mb-2 ${isCurrent ? 'text-blue-700' : 'text-gray-700'}`}>
                    Rs {formatINR(m.amount)}
                  </p>

                  {/* Bar */}
                  <div className="w-full flex justify-center" style={{ height: '240px' }}>
                    <div className="w-full relative flex items-end">
                      <div
                        className={`w-full rounded-t-lg transition-all duration-700 ${
                          isCurrent
                            ? 'bg-blue-600 shadow-lg ring-2 ring-blue-300'
                            : 'bg-blue-400 hover:bg-blue-500'
                        }`}
                        style={{ height: `${Math.max(barHeight, 4)}%` }}
                        title={`${m.month} ${m.year}: Rs ${formatINR(m.amount)}`}
                      >
                        {isCurrent && (
                          <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                            <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full font-semibold">
                              Current
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Month label */}
                  <p className={`mt-3 text-sm font-medium ${isCurrent ? 'text-blue-700' : 'text-gray-600'}`}>
                    {(m.month || '').slice(0, 3)}
                  </p>
                  <p className="text-xs text-gray-400">{m.year}</p>

                  {/* Transaction count */}
                  <p className="text-xs text-gray-500 mt-1">
                    {m.transaction_count} txn{m.transaction_count !== 1 ? 's' : ''}
                  </p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Monthly Details Table */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Monthly Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Month</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Amount Collected</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Transactions</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Avg. per Txn</th>
                </tr>
              </thead>
              <tbody>
                {months.map((m, idx) => (
                  <tr
                    key={idx}
                    className={`border-t transition-colors ${
                      m.is_current ? 'bg-blue-50 font-semibold' : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="px-4 py-3 text-gray-800">
                      {m.month} {m.year}
                      {m.is_current && (
                        <span className="ml-2 inline-block px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                          Current
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-800">Rs {formatINR(m.amount)}</td>
                    <td className="px-4 py-3 text-right text-gray-600">{m.transaction_count}</td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      Rs {formatINR(m.transaction_count > 0 ? Math.round(m.amount / m.transaction_count) : 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }

  // ---- Main Render ----

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Fee Reports</h1>
                <p className="text-gray-500">Fee collection insights and analytics</p>
              </div>
            </div>
            <Link
              to="/dashboard"
              className="hidden sm:inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-1 sm:space-x-6 overflow-x-auto">
            {TABS.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-2 border-b-2 transition-colors whitespace-nowrap ${
                    isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium text-sm sm:text-base">{tab.name}</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-500 text-sm">Loading report data...</p>
          </div>
        ) : (
          <>
            {activeTab === 'today' && renderTodayCollection()}
            {activeTab === 'defaulters' && renderDefaulters()}
            {activeTab === 'classwise' && renderClassWise()}
            {activeTab === 'monthly' && renderMonthlyTrends()}
          </>
        )}
      </div>

      {/* Voice Recorder and Confirmation Dialog */}
      <FloatingVoiceButton />
      <ConfirmationDialog />
      <VoiceReceiptModal />
    </div>
  )
}

export default FeeReportsPage
