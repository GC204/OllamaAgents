import { useState } from 'react'
import { useSessionStore } from '../store/sessionStore'
import { sessionAPI } from '../api/client'
import { ConnectionTest } from '../components/ConnectionTest'

export function HomePage() {
  const [repoName, setRepoName] = useState('')
  const [releaseBranch, setReleaseBranch] = useState('main')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const setSession = useSessionStore((state) => state.setSession)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await sessionAPI.create(repoName, releaseBranch)
      const { id } = response.data
      setSession(id, repoName, releaseBranch)
      
      // Navigate to chat page (use URL routing)
      window.location.href = `/chat/${id}`
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create session')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 rounded-lg shadow-xl p-8">
        <ConnectionTest />
        
        <h1 className="text-3xl font-bold text-white mb-2 mt-6">DevOps Agent</h1>
        <p className="text-slate-400 mb-8">Generate CI/CD pipelines with AI</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Repository Name
            </label>
            <input
              type="text"
              placeholder="owner/repo"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              required
            />
            <p className="text-xs text-slate-400 mt-1">
              GitHub repository full name (e.g., facebook/react)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Release Branch
            </label>
            <input
              type="text"
              placeholder="main"
              value={releaseBranch}
              onChange={(e) => setReleaseBranch(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !repoName}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-medium rounded transition-colors"
          >
            {loading ? 'Creating...' : 'Start Session'}
          </button>
        </form>

        <div className="mt-8 p-4 bg-slate-700/50 rounded text-sm text-slate-300 space-y-2">
          <p className="font-medium text-white">How it works:</p>
          <ol className="list-decimal list-inside space-y-1 text-xs">
            <li>Enter your GitHub repository details</li>
            <li>Provide your CI/CD requirements</li>
            <li>The AI generates a GitHub Actions workflow</li>
            <li>Review and merge to enable CI/CD</li>
          </ol>
        </div>
      </div>
    </div>
  )
}
