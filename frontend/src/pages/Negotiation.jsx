import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api'

const TERM_GUIDES = [
  {
    title: 'Lesser-of Clause',
    desc: 'Pays the lower of your billed charge or the fee schedule rate. If you bill $100 but the fee schedule says $120, you only get $100. Solution: always bill at or above fee schedule rates, and push to remove this clause.',
  },
  {
    title: 'Unilateral Amendment',
    desc: 'Allows the payer to change contract terms (including rates) with written notice but without your consent. Push for mutual amendment rights or at minimum a 90-day notice with opt-out.',
  },
  {
    title: 'Auto-Renewal',
    desc: 'The contract renews automatically unless you provide written notice within a specific window (often 60-90 days before expiration). Calendar the termination notice deadline and begin renegotiation early.',
  },
  {
    title: 'Timely Filing',
    desc: 'Claims must be submitted within a set number of days from date of service. Industry standard is 90-365 days. Anything under 90 days is aggressive. Negotiate for at least 90 days and ensure electronic filing exceptions.',
  },
  {
    title: 'Fee Schedule Types',
    desc: '"Flat fee" contracts list specific dollar amounts per code. "Percent of Medicare" contracts pay a percentage of the current Medicare rate (e.g., 110%). Percent-based contracts automatically adjust when CMS updates rates, which can be a pro or con.',
  },
]

export default function Negotiation() {
  const { id } = useParams()
  const [contract, setContract] = useState(null)
  const [letter, setLetter] = useState('')
  const [talkingPoints, setTalkingPoints] = useState([])
  const [loading, setLoading] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [copied, setCopied] = useState({ letter: false, points: false })

  useEffect(() => {
    api.get(`/contracts/${id}`).then((res) => setContract(res.data))
  }, [id])

  const generateLetter = async () => {
    setLoading(true)
    try {
      const res = await api.post(`/negotiation/${id}/letter`)
      setLetter(res.data.letter)
      setTalkingPoints(res.data.talking_points)
      setGenerated(true)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate letter')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text, key) => {
    await navigator.clipboard.writeText(text)
    setCopied({ ...copied, [key]: true })
    setTimeout(() => setCopied({ ...copied, [key]: false }), 2000)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Negotiation Tools</h1>
          <p className="text-gray-500">{contract?.payer_name}</p>
        </div>
        <Link to={`/contracts/${id}/report`}
          className="px-4 py-2 text-sm text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50">
          Back to Report
        </Link>
      </div>

      {!generated && (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center mb-8">
          <h2 className="text-xl font-semibold mb-3">Generate a Negotiation Letter</h2>
          <p className="text-gray-500 mb-6 max-w-lg mx-auto">
            Our AI will analyze your contract's underpaid codes and unfavorable terms to create
            a professional, data-driven negotiation letter and phone talking points.
          </p>
          <button onClick={generateLetter} disabled={loading}
            className="px-8 py-3 bg-amber-600 text-white rounded-lg font-semibold hover:bg-amber-700 disabled:opacity-50">
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                Generating...
              </span>
            ) : 'Generate Letter'}
          </button>
        </div>
      )}

      {generated && (
        <>
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Negotiation Letter</h2>
              <button onClick={() => copyToClipboard(letter, 'letter')}
                className="px-3 py-1 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                {copied.letter ? 'Copied!' : 'Copy to Clipboard'}
              </button>
            </div>
            <textarea
              value={letter}
              onChange={(e) => setLetter(e.target.value)}
              rows={20}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm font-mono leading-relaxed resize-y focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="text-xs text-gray-400 mt-2">You can edit this letter before copying. Changes are not saved.</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Talking Points</h2>
              <button onClick={() => copyToClipboard(talkingPoints.map((p, i) => `${i + 1}. ${p}`).join('\n'), 'points')}
                className="px-3 py-1 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
                {copied.points ? 'Copied!' : 'Copy to Clipboard'}
              </button>
            </div>
            <ul className="space-y-2">
              {talkingPoints.map((point, i) => (
                <li key={i} className="flex gap-3 text-sm">
                  <span className="text-indigo-600 font-bold mt-0.5">{i + 1}.</span>
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-6">
        <h2 className="text-lg font-semibold text-indigo-800 mb-4">Understanding Your Contract</h2>
        <div className="space-y-4">
          {TERM_GUIDES.map((g) => (
            <div key={g.title}>
              <h3 className="font-semibold text-sm text-indigo-700">{g.title}</h3>
              <p className="text-sm text-gray-600 leading-relaxed">{g.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
