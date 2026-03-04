import { Link } from 'react-router-dom'
import { useState } from 'react'

const FEATURES = [
  { title: 'Rate Gap Analysis', desc: 'See exactly which CPT codes are below Medicare and by how much, with GPCI-adjusted benchmarks for your locality.' },
  { title: 'Contract Red Flags', desc: 'AI identifies unfavorable terms — unilateral amendments, lesser-of clauses, short filing deadlines — so you know what to push back on.' },
  { title: 'Revenue Impact Estimates', desc: 'Understand the annual dollar impact of underpaid codes based on national utilization data.' },
  { title: 'Negotiation Tools', desc: 'Generate data-driven negotiation letters citing specific CPT codes and dollar gaps. Walk into payer meetings prepared.' },
]

const FAQS = [
  { q: 'What data do you use for Medicare benchmarks?', a: 'We use the 2025 CMS Physician Fee Schedule (PFS) with GPCI adjustments specific to your ZIP code locality, plus the Clinical Lab Fee Schedule (CLFS) as a fallback for lab codes. Commercial benchmarks come from UHC Transparency in Coverage data.' },
  { q: 'Is my contract data secure?', a: 'Your PDF is processed via the Anthropic API (Claude) for rate extraction and is not stored beyond the session. All data is encrypted in transit and at rest. We never share your contract data.' },
  { q: 'How accurate is the AI extraction?', a: 'Claude extracts rates with confidence scores so you can verify. The Review step lets you edit any rate before running the analysis — you always have final control over the data.' },
  { q: 'What specialties are supported?', a: 'PayerIQ works for any physician specialty. The Medicare benchmarks are CPT-code-specific and GPCI-adjusted, so they apply across Family Medicine, Internal Medicine, Surgery, Cardiology, and all other specialties.' },
]

export default function Landing() {
  const [openFaq, setOpenFaq] = useState(null)

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900 text-white">
      <nav className="max-w-6xl mx-auto px-6 py-6 flex justify-between items-center">
        <span className="text-2xl font-bold">PayerIQ</span>
        <div className="flex gap-4">
          <Link to="/login" className="px-4 py-2 text-sm rounded-lg border border-white/30 hover:bg-white/10">Login</Link>
          <Link to="/register" className="px-4 py-2 text-sm rounded-lg bg-white text-indigo-900 font-semibold hover:bg-indigo-100">Get Started</Link>
        </div>
      </nav>

      <section className="max-w-4xl mx-auto px-6 pt-24 pb-32 text-center">
        <h1 className="text-5xl font-extrabold leading-tight mb-6">
          Know if your payer contracts<br />are leaving money on the table
        </h1>
        <p className="text-xl text-indigo-200 mb-10 max-w-2xl mx-auto">
          Upload your contract PDF. PayerIQ extracts every rate, compares it to
          GPCI-adjusted Medicare benchmarks, and shows you exactly where you stand.
        </p>
        <Link to="/register" className="inline-block px-8 py-4 bg-white text-indigo-900 font-bold text-lg rounded-xl hover:bg-indigo-100 shadow-lg">
          Analyze Your First Contract Free
        </Link>
      </section>

      <section className="bg-white text-gray-900 py-20">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-10">
            <div className="text-center">
              <div className="w-14 h-14 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">1</div>
              <h3 className="font-semibold text-lg mb-2">Upload Your Contract</h3>
              <p className="text-gray-600">Drop your payer contract PDF. Our AI reads every reimbursement rate.</p>
            </div>
            <div className="text-center">
              <div className="w-14 h-14 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">2</div>
              <h3 className="font-semibold text-lg mb-2">Review & Confirm</h3>
              <p className="text-gray-600">Verify extracted CPT codes and rates. Edit anything the AI missed.</p>
            </div>
            <div className="text-center">
              <div className="w-14 h-14 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">3</div>
              <h3 className="font-semibold text-lg mb-2">Get Your Report</h3>
              <p className="text-gray-600">See every code benchmarked against your locality's Medicare rate. Export PDF.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 text-gray-900 py-20">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">What You'll Learn</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <h3 className="font-bold text-lg text-indigo-700 mb-2">{f.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-indigo-50 text-gray-900 py-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <p className="text-lg font-medium text-indigo-800 mb-2">Built on 2025 CMS Medicare data</p>
          <p className="text-gray-600">GPCI-adjusted for your locality. Commercial benchmarks from UHC Transparency in Coverage. National utilization data from Medicare PSPS.</p>
        </div>
      </section>

      <section className="bg-white text-gray-900 py-20">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {FAQS.map((faq, i) => (
              <div key={i} className="border border-gray-200 rounded-lg">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full text-left px-6 py-4 font-semibold text-gray-800 flex justify-between items-center hover:bg-gray-50"
                >
                  {faq.q}
                  <span className="text-indigo-500 text-xl">{openFaq === i ? '-' : '+'}</span>
                </button>
                {openFaq === i && (
                  <div className="px-6 pb-4 text-gray-600 text-sm leading-relaxed">{faq.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="text-center py-8 text-indigo-300 text-sm">
        PayerIQ &mdash; Financial intelligence for physician practices
      </footer>
    </div>
  )
}
