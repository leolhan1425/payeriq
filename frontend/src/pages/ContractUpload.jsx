import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api'

export default function ContractUpload() {
  const [searchParams] = useSearchParams()
  const practiceId = searchParams.get('practice_id')
  const [payerName, setPayerName] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !practiceId) return
    setUploading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('practice_id', practiceId)
      form.append('payer_name', payerName)
      form.append('file', file)
      const res = await api.post('/contracts', form)
      navigate(`/contracts/${res.data.id}/review`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Upload Payer Contract</h1>
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Payer Name</label>
            <input type="text" value={payerName} onChange={(e) => setPayerName(e.target.value)} required
              placeholder="e.g. Aetna, Blue Cross Blue Shield"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contract PDF</label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:text-indigo-700 file:font-semibold hover:file:bg-indigo-100" />
              {file && <p className="mt-2 text-sm text-gray-600">{file.name} ({(file.size / 1024).toFixed(0)} KB)</p>}
            </div>
          </div>
          <button type="submit" disabled={uploading || !file}
            className="w-full py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {uploading ? 'Uploading & Extracting...' : 'Upload & Extract Rates'}
          </button>
        </form>
        {uploading && (
          <div className="mt-4 p-4 bg-indigo-50 rounded-lg">
            <p className="text-sm text-indigo-700">AI is reading your contract and extracting reimbursement rates. This may take 30-60 seconds...</p>
          </div>
        )}
      </div>
    </div>
  )
}
