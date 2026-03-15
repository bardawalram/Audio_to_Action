import { UserIcon, CurrencyRupeeIcon } from '@heroicons/react/24/outline'

const FeeDetailsPreview = ({ data }) => {
  if (!data) return null

  const formatINR = (amt) => Number(amt).toLocaleString('en-IN')

  const getStatusColor = (status) => {
    if (status === 'PAID') return 'bg-green-100 text-green-700'
    if (status === 'PARTIAL') return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center space-x-3">
        <div className="bg-blue-100 p-2 rounded-full">
          <UserIcon className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <p className="font-bold text-gray-800">{data.student?.name}</p>
          <p className="text-sm text-gray-600">
            Roll {data.student?.roll_number} | Class {data.student?.class}
          </p>
        </div>
        <div className="ml-auto">
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusColor(data.fee_status)}`}>
            {data.fee_status}
          </span>
        </div>
      </div>

      {/* Fee Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500">Total Fees</p>
          <p className="font-bold text-gray-800">Rs. {formatINR(data.total_fees)}</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
          <p className="text-xs text-green-600">Paid</p>
          <p className="font-bold text-green-700">Rs. {formatINR(data.total_paid)}</p>
        </div>
        <div className={`rounded-lg p-3 text-center ${data.balance > 0 ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
          <p className={`text-xs ${data.balance > 0 ? 'text-red-600' : 'text-green-600'}`}>Balance</p>
          <p className={`font-bold ${data.balance > 0 ? 'text-red-700' : 'text-green-700'}`}>Rs. {formatINR(data.balance)}</p>
        </div>
      </div>

      {/* Discount if any */}
      {data.discount > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-center">
          <p className="text-xs text-purple-600">Discount Applied</p>
          <p className="font-bold text-purple-700">Rs. {formatINR(data.discount)}</p>
        </div>
      )}

      {/* Fee Breakdown */}
      {data.fee_breakdown && data.fee_breakdown.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="font-semibold text-gray-700 mb-3 flex items-center">
            <CurrencyRupeeIcon className="w-4 h-4 mr-1" />
            Fee Breakdown
          </p>
          <div className="space-y-2">
            {data.fee_breakdown.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center text-sm">
                <span className="text-gray-600">{item.name}</span>
                <div className="flex space-x-4">
                  <span className="text-gray-800">Rs. {formatINR(item.amount)}</span>
                  <span className="text-green-600">Paid: {formatINR(item.paid)}</span>
                  <span className={item.balance > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>
                    Due: {formatINR(item.balance)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Payments */}
      {data.recent_payments && data.recent_payments.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="font-semibold text-gray-700 mb-3">Recent Payments</p>
          <div className="space-y-2">
            {data.recent_payments.map((payment, idx) => (
              <div key={idx} className="flex justify-between items-center text-sm border-b border-gray-100 pb-2 last:border-0">
                <div>
                  <span className="text-blue-600 font-medium">{payment.receipt_number}</span>
                  <span className="text-gray-400 ml-2">{payment.date}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    payment.method === 'CASH' ? 'bg-green-100 text-green-700' :
                    payment.method === 'UPI' ? 'bg-purple-100 text-purple-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {payment.method}
                  </span>
                  <span className="font-bold text-gray-800">Rs. {formatINR(payment.amount)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.recent_payments && data.recent_payments.length === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center text-gray-500 text-sm">
          No payments recorded yet
        </div>
      )}
    </div>
  )
}

export default FeeDetailsPreview
