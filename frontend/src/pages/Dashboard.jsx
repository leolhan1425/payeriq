import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'

export default function Dashboard() {
  const [practices, setPractices] = useState([])
  const [contracts, setContracts] = useState([])
  const [selectedPractice, setSelectedPractice] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/practices').then((res) => {
      setPractices(res.data)
      if (res.data.length > 0) setSelectedPractice(res.data[0])
    })
  }, [])

  useEffect(() => {
    if (selectedPractice) {
      api.get(`/contracts?practice_id=${selectedPractice.id}`).then((res) => setContracts(res.data))
    }
  }, [selectedPractice])

  if (practices.length === 0) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold mb-4">Welcome to PayerIQ</h2>
        <p className="text-gray-600 mb-6">Set up your practice to get started.</p>
        <Link to="/practice" className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700">
          Set Up Practice
        </Link>
      </div>
    )
  }

  const statusColors = {
    extracting: 'bg-yellow-100 text-yellow-800',
    review: 'bg-blue-100 text-blue-800',
    compared: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-500">Practice: {selectedPractice?.name} ({selectedPractice?.zip_code})</p>
        </div>
        <Link
          to={`/contracts/new/upload?practice_id=${selectedPractice?.id}`}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700"
        >
          Upload Contract
        </Link>
      </div>

      {contracts.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center border border-gray-200">
          <p className="text-gray-500 mb-4">No contracts yet. Upload your first payer contract to get started.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Payer</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((c) => (
                <tr key={c.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-medium">{c.payer_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[c.status] || 'bg-gray-100'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    {c.status === 'review' && (
                      <Link to={`/contracts/${c.id}/review`} className="text-sm text-indigo-600 hover:underline">Review Rates</Link>
                    )}
                    {c.status === 'compared' && (
                      <Link to={`/contracts/${c.id}/report`} className="text-sm text-indigo-600 hover:underline">View Report</Link>
                    )}
                    {c.status === 'error' && (
                      <span className="text-sm text-red-500">{c.error_message}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
