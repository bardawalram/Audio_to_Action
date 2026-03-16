import { useState, useEffect, useCallback } from 'react'

const formatAmount = (amount) => {
  return new Intl.NumberFormat('en-IN').format(amount)
}

const VoiceReceiptModal = () => {
  const [visible, setVisible] = useState(false)
  const [receipt, setReceipt] = useState(null)

  const handleReceiptReady = useCallback((e) => {
    setReceipt(e.detail)
    setVisible(true)
  }, [])

  useEffect(() => {
    window.addEventListener('voiceReceiptReady', handleReceiptReady)
    return () => window.removeEventListener('voiceReceiptReady', handleReceiptReady)
  }, [handleReceiptReady])

  const handlePrint = () => {
    const r = receipt
    const printWindow = window.open('', '_blank', 'width=400,height=600')
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
        <script>window.onload = function() { window.print(); }<\/script>
      </body>
      </html>
    `)
    printWindow.document.close()
  }

  if (!visible || !receipt) return null

  return (
    <div className="fixed inset-0 z-[10001] flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-green-600 px-6 py-4 text-white text-center">
          <div className="text-3xl mb-1">&#10003;</div>
          <h2 className="text-lg font-bold">Fee Collected Successfully</h2>
        </div>

        {/* Receipt Content */}
        <div className="px-6 py-5">
          <div className="text-center mb-4">
            <span className="inline-block bg-blue-50 text-blue-700 font-bold px-4 py-2 rounded-lg text-sm">
              {receipt.receiptNumber}
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
              <span className="text-gray-500">Student</span>
              <span className="font-semibold text-gray-900">{receipt.studentName}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
              <span className="text-gray-500">Roll No</span>
              <span className="font-semibold text-gray-900">{receipt.rollNumber}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
              <span className="text-gray-500">Class</span>
              <span className="font-semibold text-gray-900">{receipt.className}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
              <span className="text-gray-500">Fee Type</span>
              <span className="font-semibold text-gray-900">{receipt.feeType}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
              <span className="text-gray-500">Payment Mode</span>
              <span className="font-semibold text-gray-900">{receipt.paymentMethod}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
              <span className="text-gray-500">Date & Time</span>
              <span className="font-semibold text-gray-900">{receipt.date} {receipt.time}</span>
            </div>
            {receipt.collectedBy && (
              <div className="flex justify-between text-sm border-b border-dashed border-gray-200 pb-2">
                <span className="text-gray-500">Collected By</span>
                <span className="font-semibold text-gray-900">{receipt.collectedBy}</span>
              </div>
            )}
            <div className="flex justify-between items-center pt-2 border-t-2 border-blue-600">
              <span className="text-base font-bold text-gray-900">Amount Paid</span>
              <span className="text-xl font-bold text-green-700">Rs. {formatAmount(receipt.amount)}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 pb-5 flex space-x-3">
          <button
            onClick={handlePrint}
            className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Print Receipt
          </button>
          <button
            onClick={() => setVisible(false)}
            className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default VoiceReceiptModal
