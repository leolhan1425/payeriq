import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api'

const TERM_EXPLANATIONS = {
  auto_renewal: 'The contract automatically renews unless terminated within the notice window. Missing the deadline locks you into another term.',
  unilateral_amendment: 'The payer can modify contract terms (including rates) without your consent. This is one of the most unfavorable provisions for providers.',
  lesser_of_clause: 'You receive the lesser of your billed charge or the fee schedule amount. If you bill below the fee schedule, you lose the difference.',
  timely_filing: 'Claims must be submitted within this many days. Shorter windows increase denial risk, especially for delayed authorizations.',
}

function ContractTerms({ contract }) {
  const [expanded, setExpanded] = useState(null)
  const hasTerms = contract.effective_date || contract.fee_schedule_type ||
    contract.auto_renewal != null || contract.unilateral_amendment != null ||
    contract.lesser_of_clause != null || contract.timely_filing_days

  if (!hasTerms) return null

  const terms = []
  if (contract.effective_date) {
    terms.push({ label: 'Effective Date', value: contract.effective_date, status: 'neutral' })
  }
  if (contract.expiration_date) {
    terms.push({ label: 'Expiration Date', value: contract.expiration_date, status: 'neutral' })
  }
  if (contract.fee_schedule_type) {
    const val = contract.fee_schedule_type === 'percent_of_medicare'
      ? `% of Medicare${contract.medicare_percentage ? ` (${contract.medicare_percentage}%)` : ''}`
      : contract.fee_schedule_type === 'flat_fee' ? 'Flat Fee' : contract.fee_schedule_type
    terms.push({ label: 'Fee Schedule Type', value: val, status: 'neutral' })
  }
  if (contract.auto_renewal != null) {
    const notice = contract.auto_renewal && contract.termination_notice_days
      ? ` (${contract.termination_notice_days}-day notice to terminate)` : ''
    terms.push({
      label: 'Auto-Renewal',
      value: (contract.auto_renewal ? 'Yes' : 'No') + notice,
      status: contract.auto_renewal ? 'warn' : 'good',
      key: 'auto_renewal',
    })
  }
  if (contract.unilateral_amendment != null) {
    terms.push({
      label: 'Unilateral Amendment',
      value: contract.unilateral_amendment ? 'Yes — payer can change terms without consent' : 'No',
      status: contract.unilateral_amendment ? 'warn' : 'good',
      key: 'unilateral_amendment',
    })
  }
  if (contract.lesser_of_clause != null) {
    terms.push({
      label: 'Lesser-of Clause',
      value: contract.lesser_of_clause ? 'Yes — pays lesser of billed charges or fee schedule' : 'No',
      status: contract.lesser_of_clause ? 'warn' : 'good',
      key: 'lesser_of_clause',
    })
  }
  if (contract.timely_filing_days) {
    const isShort = contract.timely_filing_days < 90
    terms.push({
      label: 'Timely Filing',
      value: `${contract.timely_filing_days} days${isShort ? ' — shorter than industry standard 90 days' : ''}`,
      status: isShort ? 'warn' : 'good',
      key: 'timely_filing',
    })
  }

  const warnings = terms.filter((t) => t.status === 'warn')

  return (
    <div className="mb-8">
      <h2 className="text-lg font-bold mb-3">
        Contract Terms
        {warnings.length > 0 && (
          <span className="ml-2 text-sm font-medium text-red-600">
            {warnings.length} warning{warnings.length > 1 ? 's' : ''}
          </span>
        )}
      </h2>
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {terms.map((t, i) => (
          <div key={i}>
            <div
              className={`flex items-center px-4 py-3 ${t.key ? 'cursor-pointer hover:bg-gray-50' : ''}`}
              onClick={() => t.key && setExpanded(expanded === t.key ? null : t.key)}
            >
              <span className={`w-6 text-center font-bold text-sm mr-3 ${
                t.status === 'warn' ? 'text-red-500' : t.status === 'good' ? 'text-green-500' : 'text-gray-400'
              }`}>
                {t.status === 'warn' ? '!' : t.status === 'good' ? '+' : '-'}
              </span>
              <span className="font-medium text-sm text-gray-700 w-48">{t.label}</span>
              <span className="text-sm text-gray-600 flex-1">{t.value}</span>
              {t.key && (
                <span className="text-gray-400 text-xs ml-2">{expanded === t.key ? 'hide' : 'info'}</span>
              )}
            </div>
            {expanded === t.key && TERM_EXPLANATIONS[t.key] && (
              <div className="px-4 pb-3 pl-13 text-xs text-gray-500 bg-gray-50 ml-9">
                {TERM_EXPLANATIONS[t.key]}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

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

  // Volume-weighted average % of Medicare
  const withVol = matched.filter((r) => r.national_volume > 0 && r.pct_of_medicare)
  const volWeightedPct = withVol.length > 0
    ? (withVol.reduce((sum, r) => sum + r.pct_of_medicare * r.national_volume, 0) / withVol.reduce((sum, r) => sum + r.national_volume, 0)).toFixed(1)
    : null

  // Revenue impact estimate
  const scaleFactor = 1 / 10000
  let annualImpact = 0
  for (const r of matched) {
    if (r.variance < 0 && r.national_volume > 0) {
      annualImpact += Math.abs(r.variance) * r.national_volume * scaleFactor
    }
  }
  annualImpact = annualImpact > 0 ? annualImpact : null

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Contract Analysis Report</h1>
          <p className="text-gray-500">{contract?.payer_name}</p>
        </div>
        <div className="flex gap-3">
          <Link to={`/contracts/${id}/negotiate`}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg font-semibold hover:bg-amber-700">
            Generate Negotiation Letter
          </Link>
          <button onClick={downloadPdf} className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700">
            Download PDF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
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
        {volWeightedPct && (
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className={`text-2xl font-bold ${parseFloat(volWeightedPct) < 100 ? 'text-red-600' : 'text-green-600'}`}>{volWeightedPct}%</div>
            <div className="text-sm text-gray-500">Volume-Weighted Avg</div>
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

      {/* Revenue Impact Card */}
      {annualImpact && (
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 mb-8">
          <div className="flex items-baseline gap-3 mb-2">
            <span className="text-3xl font-bold text-red-600">${Math.round(annualImpact).toLocaleString()}</span>
            <span className="text-lg font-semibold text-red-700">Estimated Annual Impact</span>
          </div>
          <p className="text-sm text-red-600/70">
            Based on national Medicare utilization data scaled to a solo practice (~1/10,000 of national volume).
            Actual impact varies by practice size, payer mix, and case volume. This is a directional estimate.
          </p>
        </div>
      )}

      {/* Contract Terms */}
      {contract && <ContractTerms contract={contract} />}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-6">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">CPT</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Description</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Contract</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Medicare</th>
              <th className="text-center px-4 py-3 text-sm font-medium text-gray-500">Source</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Variance</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">% Medicare</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Comm Avg</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">% Comm</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">Natl Volume</th>
            </tr>
          </thead>
          <tbody>
            {matched.sort((a, b) => (a.pct_of_medicare || 0) - (b.pct_of_medicare || 0)).map((r) => (
              <tr key={r.id} className="border-t border-gray-100">
                <td className="px-4 py-3 font-mono text-sm">{r.cpt_code}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{r.description}</td>
                <td className="px-4 py-3 text-right text-sm">${r.contracted_rate.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-sm">${r.medicare_rate.toFixed(2)}</td>
                <td className="px-4 py-3 text-center text-xs text-gray-400">{r.benchmark_source}</td>
                <td className={`px-4 py-3 text-right text-sm font-medium ${r.variance < 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ${r.variance.toFixed(2)}
                </td>
                <td className={`px-4 py-3 text-right text-sm font-medium ${(r.pct_of_medicare || 0) < 100 ? 'text-red-600' : 'text-green-600'}`}>
                  {r.pct_of_medicare}%
                </td>
                <td className="px-4 py-3 text-right text-sm text-gray-500">
                  {r.commercial_avg_rate ? `$${r.commercial_avg_rate.toFixed(2)}` : ''}
                </td>
                <td className={`px-4 py-3 text-right text-sm font-medium ${r.pct_of_commercial && r.pct_of_commercial < 100 ? 'text-red-600' : r.pct_of_commercial ? 'text-green-600' : ''}`}>
                  {r.pct_of_commercial ? `${r.pct_of_commercial}%` : ''}
                </td>
                <td className="px-4 py-3 text-right text-xs text-gray-400">
                  {r.national_volume ? r.national_volume.toLocaleString() : ''}
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
