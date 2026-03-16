import { CurrencyRupeeIcon, ReceiptPercentIcon } from '@heroicons/react/24/outline'

const TodayCollectionPreview = ({ data }) => {
  if (!data) return null

  const formatINR = (amt) => Number(amt).toLocaleString('en-IN')

  const methodLabels = {
    CASH: 'Cash',
    UPI: 'UPI',
    CARD: 'Card',
    CHEQUE: 'Cheque',
    ONLINE: 'Online',
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <CurrencyRupeeIcon className="w-5 h-5 text-green-600" />
          <p className="font-semibold text-green-800">{data.message}</p>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-3">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-700">
              Rs. {formatINR(data.total_collected)}
            </p>
            <p className="text-xs text-gray-500">Total Collected</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-700">
              {data.transaction_count}
            </p>
            <p className="text-xs text-gray-500">Transactions</p>
          </div>
        </div>
      </div>

      {/* By Payment Method */}
      {data.by_payment_method && data.by_payment_method.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {data.by_payment_method.map((method, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500">
                {methodLabels[method.payment_method] || method.payment_method}
              </p>
              <p className="font-bold text-gray-900">
                Rs. {formatINR(method.total)}
              </p>
              <p className="text-xs text-gray-400">{method.count} txns</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TodayCollectionPreview
