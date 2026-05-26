import { useEffect, useState } from 'react'

export function ConnectionTest() {
  const [status, setStatus] = useState<string>('Testing...')
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await fetch('http://localhost:8000/health')
        const data = await response.json()
        setStatus(`✅ Backend Connected: ${JSON.stringify(data)}`)
      } catch (err: any) {
        setError(`❌ Connection Failed: ${err.message}`)
      }
    }

    testConnection()
  }, [])

  return (
    <div style={{ padding: '20px', margin: '10px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
      <h3>Backend Connection Status:</h3>
      {status && <p style={{ color: 'green' }}>{status}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <p style={{ fontSize: '12px', color: '#666' }}>
        Testing endpoint: http://localhost:8000/health
      </p>
      <button 
        onClick={() => {
          setStatus('Testing...')
          setError('')
          window.location.reload()
        }}
        style={{
          padding: '10px 20px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        Refresh Page
      </button>
    </div>
  )
}
