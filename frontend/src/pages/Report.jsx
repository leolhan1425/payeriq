import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'

export default function Report() {
  const { id } = useParams()
  const [contract, setContract] = useState(null)
  const [rates, setRates] = useState([])
  const [loading, setLoading] = useState(true)

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
  }, [id])

  const downloadPdf = () => {
    const token = localStorage.getItem('token')
    window.open(`/api/reports/${id}/pdf?token=${token}`, '_blank')
  }

  if (loading) {
    return <div className="text-center py-20 text-gray-500">Loading report...</div>
  }

  const matched = rates.filter((r) => r.medicare_rate != null)
  const unmatched = rates.filter((r) => r.medicare_rate == null)
  const avgPct = matched.length > 0
    ? (matched.reduce((sum, r) => sum + (r.pct_of_medicare || 0), 0) / matched.length).toFixed(1)
    : null
  const totalVariance = matched.reduce((sum, r) => sum + (r.variance || 0), 0).toFixed(2)
  const belowCount = matched.filter((r) => (r.pct_of_medicare || 0) < 100).length

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Contract Analysis Report</h1>
          <p className="text-gray-500">{contract?.payer_name}</p>
        </div>
        <button onClick={downloadPdf} className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700">
          Download PDF
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-2xl font-bold text-indigo-700">{matched.length}</div>
          <div className="text-sm text-gray-500">Codes Matched</div>
        </div>
        {avgPct && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className={`text-2xl font-bold ${parseFloat(avgPct) < 100 ? 'text-red-600' : 'text-green-600'}`}>{avgPct}%</div>
            <div className="text-sm text-gray-500">Avg % of Medicare</div>
          </div>
        )}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className={`text-2xl font-bold ${parseFloat(totalVariance) < 0 ? 'text-red-600' : 'text-green-600'}`}>${totalVariance}</div>
          <div className="text-sm text-gray-500">Total Variance</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-2xl font-bold text-red-600">{belowCount}</div>
          <div className="text-sm text-gray-500">Below Medicare</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-6">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">CPT</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Description</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Contract</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Medicare</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Variance</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">% Medicare</th>
            </tr>
          </thead>
          <tbody>
            {matched.sort((a, b) => (a.pct_of_medicare || 0) - (b.pct_of_medicare || 0)).map((r) => (
              <tr key={r.id} className="border-t border-gray-100">
                <td className="px-4 py-3 font-mono text-sm">{r.cpt_code}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{r.description}</td>
                <td className="px-4 py-3 text-right text-sm">${r.contracted_rate.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-sm">${r.medicare_rate.toFixed(2)}</td>
                <td className={`px-4 py-3 text-right text-sm font-medium ${r.variance < 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ${r.variance.toFixed(2)}
                </td>
                <td className={`px-4 py-3 text-right text-sm font-medium ${(r.pct_of_medicare || 0) < 100 ? 'text-red-600' : 'text-green-600'}`}>
                  {r.pct_of_medicare}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {unmatched.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-yellow-50 border-b border-yellow-100">
            <span className="text-sm font-medium text-yellow-800">{unmatched.length} Unmatched Codes</span>
          </div>
          <table className="w-full">
            <tbody>
              {unmatched.map((r) => (
                <tr key={r.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-mono text-sm">{r.cpt_code}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{r.description}</td>
                  <td className="px-4 py-3 text-right text-sm">${r.contracted_rate.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
