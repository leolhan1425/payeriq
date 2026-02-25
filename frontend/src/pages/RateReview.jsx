import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'

export default function RateReview() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState(null)
  const [rates, setRates] = useState([])
  const [loading, setLoading] = useState(true)
  const [comparing, setComparing] = useState(false)

  useEffect(() => {
    const load = async () => {
      const [contractRes, ratesRes] = await Promise.all([
        api.get(`/contracts/${id}`),
        api.get(`/rates/contract/${id}`),
      ])
      setContract(contractRes.data)
      setRates(ratesRes.data)
      setLoading(false)
    }
    load()
    // Poll if still extracting
    const interval = setInterval(async () => {
      const res = await api.get(`/contracts/${id}`)
      if (res.data.status !== 'extracting') {
        clearInterval(interval)
        setContract(res.data)
        const ratesRes = await api.get(`/rates/contract/${id}`)
        setRates(ratesRes.data)
        setLoading(false)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [id])

  const updateRate = async (rateId, field, value) => {
    await api.put(`/rates/${rateId}`, { [field]: value })
    setRates(rates.map((r) => (r.id === rateId ? { ...r, [field]: value } : r)))
  }

  const deleteRate = async (rateId) => {
    await api.delete(`/rates/${rateId}`)
    setRates(rates.filter((r) => r.id !== rateId))
  }

  const runComparison = async () => {
    setComparing(true)
    await api.post(`/reports/${id}/compare`)
    navigate(`/contracts/${id}/report`)
  }

  if (loading || contract?.status === 'extracting') {
    return (
      <div className="text-center py-20">
        <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-600">Extracting rates from contract...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Review Extracted Rates</h1>
          <p className="text-gray-500">{contract?.payer_name} &mdash; {rates.length} rates found</p>
        </div>
        <button onClick={runComparison} disabled={comparing || rates.length === 0}
          className="px-6 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50">
          {comparing ? 'Comparing...' : 'Compare to Medicare'}
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">CPT Code</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Description</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Modifier</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Rate</th>
              <th className="text-center px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rates.map((r) => (
              <tr key={r.id} className="border-t border-gray-100">
                <td className="px-4 py-3">
                  <input value={r.cpt_code} onChange={(e) => updateRate(r.id, 'cpt_code', e.target.value)}
                    className="w-24 px-2 py-1 border border-gray-200 rounded text-sm" />
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{r.description}</td>
                <td className="px-4 py-3">
                  <input value={r.modifier || ''} onChange={(e) => updateRate(r.id, 'modifier', e.target.value || null)}
                    className="w-16 px-2 py-1 border border-gray-200 rounded text-sm" />
                </td>
                <td className="px-4 py-3 text-right">
                  <input type="number" step="0.01" value={r.contracted_rate}
                    onChange={(e) => updateRate(r.id, 'contracted_rate', parseFloat(e.target.value))}
                    className="w-24 px-2 py-1 border border-gray-200 rounded text-sm text-right" />
                </td>
                <td className="px-4 py-3 text-center">
                  <button onClick={() => deleteRate(r.id)} className="text-red-500 hover:text-red-700 text-sm">Remove</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
