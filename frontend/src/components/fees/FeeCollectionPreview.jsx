import { useState } from 'react'
import { CurrencyRupeeIcon, UserIcon } from '@heroicons/react/24/outline'

const FeeCollectionPreview = ({ data, onUpdate }) => {
  const [editedAmount, setEditedAmount] = useState(data?.amount || 0)
  const [editedMethod, setEditedMethod] = useState(data?.payment_method || 'CASH')

  const handleAmountChange = (e) => {
    const newAmount = Number(e.target.value)
    setEditedAmount(newAmount)
    if (onUpdate) {
      onUpdate({ ...data, amount: newAmount, payment_method: editedMethod })
    }
  }

  const handleMethodChange = (e) => {
    const newMethod = e.target.value
    setEditedMethod(newMethod)
    if (onUpdate) {
      onUpdate({ ...data, amount: editedAmount, payment_method: newMethod })
    }
  }

  if (!data) return null

  const formatINR = (amt) => Number(amt).toLocaleString('en-IN')

  return (
    <div className="space-y-4">
      {/* Student Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center space-x-3 mb-3">
          <div className="bg-blue-100 p-2 rounded-full">
            <UserIcon className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{data.student?.name}</p>
            <p className="text-sm text-gray-600">
              Roll {data.student?.roll_number} | Class {data.student?.class}
            </p>
          </div>
        </div>
      </div>

      {/* Fee Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500">Total Fees</p>
          <p className="font-bold text-gray-900">Rs. {formatINR(data.total_fees)}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500">Already Paid</p>
          <p className="font-bold text-green-700">Rs. {formatINR(data.already_paid)}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-500">Balance</p>
          <p className="font-bold text-red-700">Rs. {formatINR(data.balance_before)}</p>
        </div>
      </div>

      {/* Editable Collection Details */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <CurrencyRupeeIcon className="w-5 h-5 text-green-600" />
          <p className="font-semibold text-green-800">Collection Details</p>
        </div>

        {/* Fee Type Badge */}
        {data.fee_type_display && (
          <div className="mb-3">
            <label className="text-xs text-gray-600 block mb-1">Fee Type</label>
            <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold border border-green-300">
              {data.fee_type_display}
            </span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-600 block mb-1">Amount</label>
            <input
              type="number"
              value={editedAmount}
              onChange={handleAmountChange}
              min="1"
              max={data.balance_before}
              className="w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent font-bold text-green-800"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600 block mb-1">Payment Method</label>
            <select
              value={editedMethod}
              onChange={handleMethodChange}
              className="w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent font-medium"
            >
              <option value="CASH">Cash</option>
              <option value="UPI">UPI</option>
              <option value="CARD">Card</option>
              <option value="CHEQUE">Cheque</option>
              <option value="ONLINE">Online</option>
            </select>
          </div>
        </div>

        {/* Balance after */}
        <div className="mt-3 pt-3 border-t border-green-200">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Balance after payment:</span>
            <span className="font-bold text-gray-900">
              Rs. {formatINR(Math.max(0, data.balance_before - editedAmount))}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FeeCollectionPreview
