import { ArrowRightIcon, FolderIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

const NavigationPreview = ({ data }) => {
  const { navigation_type, page_type, class_name, message, url } = data

  return (
    <div className="space-y-4">
      {/* Navigation Type Badge */}
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-purple-100 rounded-lg">
          {navigation_type === 'sheet' ? (
            <DocumentTextIcon className="w-6 h-6 text-purple-600" />
          ) : (
            <FolderIcon className="w-6 h-6 text-purple-600" />
          )}
        </div>
        <div>
          <p className="text-sm text-gray-600">Navigation Type</p>
          <p className="font-semibold text-gray-900 capitalize">
            {navigation_type === 'sheet' ? 'Class Sheet' : 'List Page'}
          </p>
        </div>
      </div>

      {/* Destination */}
      <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-purple-700 font-medium mb-1">Destination:</p>
            <p className="text-lg font-bold text-purple-900 capitalize">
              {page_type} {navigation_type === 'sheet' && class_name && `- Class ${class_name}`}
            </p>
            <p className="text-sm text-gray-600 mt-2">{message}</p>
          </div>
          <ArrowRightIcon className="w-8 h-8 text-purple-600" />
        </div>
      </div>

      {/* URL Path */}
      <div className="text-sm">
        <span className="text-gray-600">Path: </span>
        <code className="bg-gray-100 px-2 py-1 rounded text-gray-800">{url}</code>
      </div>
    </div>
  )
}

export default NavigationPreview
