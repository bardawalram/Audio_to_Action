import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

const DefaultersPreview = ({ data }) => {
  if (!data) return null

  const formatINR = (amt) => Number(amt).toLocaleString('en-IN')

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
          <p className="font-semibold text-red-800">{data.message}</p>
        </div>
        <p className="text-sm text-red-600">
          Total defaulters: {data.total_count}
        </p>
      </div>

      {/* Defaulters Table */}
      {data.defaulters && data.defaulters.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-600">
                <th className="px-3 py-2 text-left">Roll</th>
                <th className="px-3 py-2 text-left">Student</th>
                <th className="px-3 py-2 text-left">Class</th>
                <th className="px-3 py-2 text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              {data.defaulters.map((d, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-700">{d.roll_number}</td>
                  <td className="px-3 py-2 font-medium text-gray-900">{d.name}</td>
                  <td className="px-3 py-2 text-gray-600">{d.class_name}</td>
                  <td className="px-3 py-2 text-right font-bold text-red-600">
                    Rs. {formatINR(d.balance)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.total_count > 20 && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Showing top 20 of {data.total_count} defaulters
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default DefaultersPreview
