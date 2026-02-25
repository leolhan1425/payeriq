import { Link } from 'react-router-dom'

export default function Landing() {
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

      <footer className="text-center py-8 text-indigo-300 text-sm">
        PayerIQ &mdash; Financial intelligence for physician practices
      </footer>
    </div>
  )
}
