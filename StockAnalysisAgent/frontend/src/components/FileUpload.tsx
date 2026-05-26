import { useState, useRef } from 'react'
import { uploadFile } from '../api/client'

const ALLOWED = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv']

export function FileUpload({ onUploaded }: { onUploaded?: (name: string, chunks: number) => void }) {
  const [status, setStatus] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function accept(f: File): boolean {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    return ALLOWED.includes(ext)
  }

  async function doUpload(file: File) {
    if (!accept(file)) {
      setStatus('Unsupported type. Use: PDF, DOCX, XLSX, CSV')
      return
    }
    setStatus('Uploading...')
    const result = await uploadFile(file)
    if (result.ok) {
      setStatus(`Ingested: ${file.name}${result.chunks != null ? ` (${result.chunks} chunks)` : ''}`)
      onUploaded?.(file.name, result.chunks ?? 0)
    } else {
      setStatus(result.message ?? 'Upload failed')
    }
    setTimeout(() => setStatus(null), 4000)
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) doUpload(f)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      style={{
        padding: '0.5rem 0.75rem',
        border: `1px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: '8px',
        background: dragging ? 'var(--surface)' : 'transparent',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        flexWrap: 'wrap',
      }}
    >
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        style={{
          background: 'var(--accent)',
          color: 'white',
          border: 'none',
          padding: '0.4rem 0.75rem',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '0.9rem',
        }}
      >
        Upload file
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED.join(',')}
        style={{ display: 'none' }}
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) doUpload(f)
          e.target.value = ''
        }}
      />
      <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
        {status ?? 'PDF, DOCX, XLSX, CSV — or drag here'}
      </span>
    </div>
  )
}
