import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function PracticeSetup() {
  const [name, setName] = useState('')
  const [zip, setZip] = useState('')
  const [practices, setPractices] = useState([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/practices').then((res) => setPractices(res.data))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await api.post('/practices', { name, zip_code: zip })
      setPractices([...practices, res.data])
      setName('')
      setZip('')
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create practice')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Practice Setup</h1>

      {practices.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Your Practices</h2>
          <div className="space-y-2">
            {practices.map((p) => (
              <div key={p.id} className="bg-white rounded-lg border border-gray-200 p-4 flex justify-between items-center">
                <div>
                  <div className="font-medium">{p.name}</div>
                  <div className="text-sm text-gray-500">ZIP: {p.zip_code} | GPCI Locality: {p.gpci_locality || 'Not resolved'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Add New Practice</h2>
        {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Practice Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required
              placeholder="e.g. Family Medicine Associates"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
            <input type="text" value={zip} onChange={(e) => setZip(e.target.value)} required maxLength={5} pattern="\d{5}"
              placeholder="e.g. 97201"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" />
            <p className="text-xs text-gray-400 mt-1">Used to look up your GPCI locality for Medicare rate adjustments</p>
          </div>
          <button type="submit" className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700">
            Create Practice
          </button>
        </form>
      </div>
    </div>
  )
}
