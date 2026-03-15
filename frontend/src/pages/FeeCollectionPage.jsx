import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  UserGroupIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import {
  CurrencyRupeeIcon,
  CheckBadgeIcon,
  PrinterIcon,
} from '@heroicons/react/24/solid'
import FloatingVoiceButton from '../components/voice/FloatingVoiceButton'
import ConfirmationDialog from '../components/voice/ConfirmationDialog'
import VoiceReceiptModal from '../components/voice/VoiceReceiptModal'
import feeService from '../services/feeService'

const formatAmount = (amount) => {
  return new Intl.NumberFormat('en-IN').format(amount)
}

const FeeCollectionPage = () => {
  const { classNum, section } = useParams()
  const navigate = useNavigate()
  const dispatch = useDispatch()

  const [students, setStudents] = useState([])
  const [feeStructures, setFeeStructures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Collection modal state
  const [showModal, setShowModal] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [selectedFeeStructure, setSelectedFeeStructure] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('CASH')
  const [remarks, setRemarks] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Notification state
  const [notification, setNotification] = useState(null)

  // Receipt state
  const [receiptData, setReceiptData] = useState(null)
  const [showReceipt, setShowReceipt] = useState(false)

  const fetchStudents = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await feeService.getStudentFeeStatus(classNum, section)
      const data = response.data
      setStudents(data.students || [])
      setFeeStructures(data.fee_structures || [])
    } catch (err) {
      console.error('Failed to fetch student fee status:', err)
      setError('Failed to load student fee data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (classNum && section) {
      fetchStudents()
    }
  }, [classNum, section])

  // Refresh data when fee is collected via voice command
  useEffect(() => {
    const handleFeeCollected = () => {
      console.log('Fee collected via voice — refreshing student data')
      fetchStudents()
    }
    window.addEventListener('feeCollected', handleFeeCollected)
    return () => window.removeEventListener('feeCollected', handleFeeCollected)
  }, [classNum, section])

  // Auto-dismiss notification
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [notification])

  // Summary calculations
  const totalStudents = students.length
  const fullyPaid = students.filter((s) => s.status === 'PAID').length
  const partialPaid = students.filter((s) => s.status === 'PARTIAL').length
  const pending = students.filter((s) => s.status === 'PENDING').length

  const handleCollectClick = (student) => {
    setSelectedStudent(student)
    setPaymentAmount(student.balance || '')
    setSelectedFeeStructure(feeStructures.length > 0 ? feeStructures[0].id : '')
    setPaymentMethod('CASH')
    setRemarks('')
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setSelectedStudent(null)
    setPaymentAmount('')
    setSelectedFeeStructure('')
    setPaymentMethod('CASH')
    setRemarks('')
  }

  const handleSubmitPayment = async (e) => {
    e.preventDefault()

    if (!paymentAmount || Number(paymentAmount) <= 0) {
      setNotification({ type: 'error', message: 'Please enter a valid amount.' })
      return
    }

    if (!selectedFeeStructure) {
      setNotification({ type: 'error', message: 'Please select a fee structure.' })
      return
    }

    try {
      setSubmitting(true)
      const fsObj = feeStructures.find((f) => String(f.id) === String(selectedFeeStructure))
      const response = await feeService.collectFee({
        student_id: selectedStudent.student_id || selectedStudent.id,
        fee_structure_id: selectedFeeStructure,
        amount: Number(paymentAmount),
        payment_method: paymentMethod,
        remarks: remarks.trim(),
      })

      const payment = response.data?.payment || {}
      const receiptNumber = response.data?.receipt_number || payment.receipt_number || 'N/A'

      // Build receipt data
      setReceiptData({
        receiptNumber,
        studentName: selectedStudent.student_name || selectedStudent.name,
        rollNumber: selectedStudent.roll_number,
        className: `Class ${classNum}${section}`,
        feeType: fsObj ? `${fsObj.fee_type_display} (${fsObj.term_display})` : 'Fee',
        amount: Number(paymentAmount),
        paymentMethod,
        date: new Date().toLocaleDateString('en-IN', {
          day: '2-digit', month: 'short', year: 'numeric',
        }),
        time: new Date().toLocaleTimeString('en-IN', {
          hour: '2-digit', minute: '2-digit',
        }),
        collectedBy: payment.collected_by_name || 'Accountant',
      })
      setShowReceipt(true)

      handleCloseModal()
      await fetchStudents()
    } catch (err) {
      console.error('Fee collection failed:', err)
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.message ||
        'Failed to collect fee. Please try again.'
      setNotification({ type: 'error', message: errorMsg })
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PAID':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            PAID
          </span>
        )
      case 'PARTIAL':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            PARTIAL
          </span>
        )
      case 'PENDING':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            PENDING
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {status}
          </span>
        )
    }
  }

  const handlePrintReceipt = () => {
    const printWindow = window.open('', '_blank', 'width=400,height=600')
    const r = receiptData
    printWindow.document.write(`
      <html>
      <head>
        <title>Fee Receipt - ${r.receiptNumber}</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
          .receipt { max-width: 350px; margin: 0 auto; border: 2px solid #1e40af; padding: 20px; }
          .header { text-align: center; border-bottom: 2px solid #1e40af; padding-bottom: 12px; margin-bottom: 16px; }
          .header h1 { margin: 0; font-size: 20px; color: #1e40af; }
          .header p { margin: 4px 0 0; font-size: 12px; color: #666; }
          .receipt-no { text-align: center; background: #eff6ff; padding: 8px; margin-bottom: 16px; border-radius: 4px; font-weight: bold; color: #1e40af; font-size: 14px; }
          .row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px dashed #e5e7eb; }
          .row:last-child { border-bottom: none; }
          .label { color: #6b7280; }
          .value { font-weight: 600; text-align: right; }
          .amount-row { display: flex; justify-content: space-between; padding: 12px 0; margin-top: 8px; border-top: 2px solid #1e40af; font-size: 16px; font-weight: bold; }
          .amount-row .value { color: #059669; }
          .footer { text-align: center; margin-top: 20px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; }
          .stamp { text-align: center; margin-top: 16px; padding: 6px; border: 1px solid #059669; color: #059669; font-weight: bold; font-size: 12px; border-radius: 4px; }
          @media print { body { padding: 0; } .receipt { border: 1px solid #000; } }
        </style>
      </head>
      <body>
        <div class="receipt">
          <div class="header">
            <h1>ReATOA School</h1>
            <p>Fee Payment Receipt</p>
          </div>
          <div class="receipt-no">${r.receiptNumber}</div>
          <div class="row"><span class="label">Date</span><span class="value">${r.date} ${r.time}</span></div>
          <div class="row"><span class="label">Student</span><span class="value">${r.studentName}</span></div>
          <div class="row"><span class="label">Roll No</span><span class="value">${r.rollNumber}</span></div>
          <div class="row"><span class="label">Class</span><span class="value">${r.className}</span></div>
          <div class="row"><span class="label">Fee Type</span><span class="value">${r.feeType}</span></div>
          <div class="row"><span class="label">Payment Mode</span><span class="value">${r.paymentMethod}</span></div>
          <div class="amount-row"><span>Amount Paid</span><span class="value">Rs. ${formatAmount(r.amount)}</span></div>
          <div class="stamp">PAID</div>
          <div class="footer">
            <p>Collected by: ${r.collectedBy}</p>
            <p>This is a computer-generated receipt</p>
          </div>
        </div>
        <script>window.onload = function() { window.print(); }</script>
      </body>
      </html>
    `)
    printWindow.document.close()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification */}
      {notification && (
        <div
          className={`fixed top-4 right-4 z-50 max-w-md px-4 py-3 rounded-lg shadow-lg flex items-center space-x-3 ${
            notification.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckBadgeIcon className="w-6 h-6 text-green-500 flex-shrink-0" />
          ) : (
            <ExclamationTriangleIcon className="w-6 h-6 text-red-500 flex-shrink-0" />
          )}
          <p className="text-sm font-medium">{notification.message}</p>
          <button
            onClick={() => setNotification(null)}
            className="ml-auto flex-shrink-0 text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/fees')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="w-6 h-6 text-gray-600" />
            </button>
            <div>
              <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                <Link to="/dashboard" className="hover:text-blue-600 transition-colors">
                  Dashboard
                </Link>
                <ChevronRightIcon className="w-4 h-4" />
                <Link to="/fees" className="hover:text-blue-600 transition-colors">
                  Fee Collection
                </Link>
                <ChevronRightIcon className="w-4 h-4" />
                <span className="text-gray-900 font-medium">
                  Class {classNum}
                  {section}
                </span>
              </nav>
              <h1 className="text-3xl font-bold text-gray-900">
                Fee Collection - Class {classNum}
                {section}
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="ml-4 text-gray-600 text-lg">Loading student data...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <p className="text-red-700 font-medium">{error}</p>
            <button
              onClick={fetchStudents}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Total Students</p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">{totalStudents}</p>
                  </div>
                  <div className="bg-blue-100 p-3 rounded-full">
                    <UserGroupIcon className="w-8 h-8 text-blue-600" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Fully Paid</p>
                    <p className="text-3xl font-bold text-green-600 mt-1">{fullyPaid}</p>
                  </div>
                  <div className="bg-green-100 p-3 rounded-full">
                    <CheckCircleIcon className="w-8 h-8 text-green-600" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Partial</p>
                    <p className="text-3xl font-bold text-yellow-600 mt-1">{partialPaid}</p>
                  </div>
                  <div className="bg-yellow-100 p-3 rounded-full">
                    <ClockIcon className="w-8 h-8 text-yellow-600" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Pending</p>
                    <p className="text-3xl font-bold text-red-600 mt-1">{pending}</p>
                  </div>
                  <div className="bg-red-100 p-3 rounded-full">
                    <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Student Table */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Student Fee Status</h2>
              </div>

              {students.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <UserGroupIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No students found for this class/section.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Roll No
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Student Name
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Fees
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Paid
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Balance
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Action
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {students.map((student) => (
                        <tr
                          key={student.student_id || student.id}
                          className="hover:bg-gray-50 transition-colors"
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {student.roll_number}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {student.student_name || student.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                            Rs. {formatAmount(student.total_fees)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-green-700 text-right font-medium">
                            Rs. {formatAmount(student.total_paid)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-red-700 text-right font-medium">
                            Rs. {formatAmount(student.balance)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center">
                            {getStatusBadge(student.status)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center">
                            <button
                              onClick={() => handleCollectClick(student)}
                              disabled={student.status === 'PAID'}
                              className={`inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                student.status === 'PAID'
                                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                  : 'bg-blue-600 text-white hover:bg-blue-700'
                              }`}
                            >
                              <CurrencyRupeeIcon className="w-4 h-4 mr-1" />
                              Collect
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Collection Modal */}
      {showModal && selectedStudent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
            {/* Modal Header */}
            <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg flex items-center justify-between">
              <h2 className="text-xl font-bold">Collect Fee</h2>
              <button
                onClick={handleCloseModal}
                className="text-white hover:text-blue-200 transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Student Info */}
            <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
              <p className="text-lg font-semibold text-gray-900">{selectedStudent.student_name || selectedStudent.name}</p>
              <p className="text-sm text-gray-600">
                Class {classNum}
                {section} | Roll No: {selectedStudent.roll_number}
              </p>
              <div className="mt-2 flex items-center space-x-4 text-sm">
                <span className="text-gray-500">
                  Balance:{' '}
                  <span className="font-semibold text-red-600">
                    Rs. {formatAmount(selectedStudent.balance)}
                  </span>
                </span>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmitPayment} className="px-6 py-4 space-y-4">
              {/* Fee Structure */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fee Structure
                </label>
                <select
                  value={selectedFeeStructure}
                  onChange={(e) => setSelectedFeeStructure(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select Fee Structure</option>
                  {feeStructures.map((fs) => (
                    <option key={fs.id} value={fs.id}>
                      {fs.fee_type_display} ({fs.term_display}) - Rs. {formatAmount(fs.amount)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount (Rs.)
                </label>
                <input
                  type="number"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  min="1"
                  max={selectedStudent.balance}
                  placeholder="Enter amount"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Payment Method */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Method
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="CASH">Cash</option>
                  <option value="UPI">UPI</option>
                  <option value="CARD">Card</option>
                  <option value="CHEQUE">Cheque</option>
                  <option value="ONLINE">Online</option>
                </select>
              </div>

              {/* Remarks */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Remarks (Optional)
                </label>
                <textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  rows={3}
                  placeholder="Add any remarks..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Buttons */}
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  disabled={submitting}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircleIcon className="w-5 h-5" />
                      <span>Submit Payment</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Receipt Modal */}
      {showReceipt && receiptData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            {/* Receipt Header */}
            <div className="bg-green-600 text-white px-6 py-4 rounded-t-lg flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckBadgeIcon className="w-6 h-6" />
                <h2 className="text-xl font-bold">Payment Successful</h2>
              </div>
              <button
                onClick={() => setShowReceipt(false)}
                className="text-white hover:text-green-200 transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Receipt Content */}
            <div className="px-6 py-5">
              <div className="text-center mb-4">
                <p className="text-sm text-gray-500">Receipt Number</p>
                <p className="text-xl font-bold text-blue-600">{receiptData.receiptNumber}</p>
              </div>

              <div className="border border-gray-200 rounded-lg divide-y divide-gray-100">
                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">Student</span>
                  <span className="text-sm font-semibold text-gray-900">{receiptData.studentName}</span>
                </div>
                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">Roll No</span>
                  <span className="text-sm font-semibold text-gray-900">{receiptData.rollNumber}</span>
                </div>
                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">Class</span>
                  <span className="text-sm font-semibold text-gray-900">{receiptData.className}</span>
                </div>
                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">Fee Type</span>
                  <span className="text-sm font-semibold text-gray-900">{receiptData.feeType}</span>
                </div>
                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">Payment Mode</span>
                  <span className="text-sm font-semibold text-gray-900">{receiptData.paymentMethod}</span>
                </div>
                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">Date & Time</span>
                  <span className="text-sm font-semibold text-gray-900">{receiptData.date} {receiptData.time}</span>
                </div>
                <div className="flex justify-between px-4 py-3 bg-green-50">
                  <span className="text-base font-semibold text-gray-700">Amount Paid</span>
                  <span className="text-lg font-bold text-green-700">Rs. {formatAmount(receiptData.amount)}</span>
                </div>
              </div>
            </div>

            {/* Receipt Actions */}
            <div className="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-between">
              <button
                onClick={() => setShowReceipt(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
              <button
                onClick={handlePrintReceipt}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <PrinterIcon className="w-5 h-5" />
                <span>Print Receipt</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Voice Components */}
      <FloatingVoiceButton />
      <ConfirmationDialog />
      <VoiceReceiptModal />
    </div>
  )
}

export default FeeCollectionPage
