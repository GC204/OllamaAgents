import { create } from 'zustand'

export interface Session {
  sessionId: string
  repoName: string
  releaseBranch: string
}

export interface SessionState {
  sessionId: string | null
  repoName: string | null
  releaseBranch: string | null
  status: 'idle' | 'loading' | 'analyzing' | 'generating' | 'error'
  error: string | null
  
  session: Session | null
  setSession: (sessionId: string, repoName: string, releaseBranch: string) => void
  setStatus: (status: SessionState['status']) => void
  setError: (error: string | null) => void
  clearSession: () => void
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessionId: localStorage.getItem('sessionId'),
  repoName: localStorage.getItem('repoName'),
  releaseBranch: localStorage.getItem('releaseBranch'),
  status: 'idle',
  error: null,
  
  get session() {
    const state = get()
    if (state.sessionId && state.repoName && state.releaseBranch) {
      return {
        sessionId: state.sessionId,
        repoName: state.repoName,
        releaseBranch: state.releaseBranch,
      }
    }
    return null
  },

  setSession: (sessionId, repoName, releaseBranch) => {
    localStorage.setItem('sessionId', sessionId)
    localStorage.setItem('repoName', repoName)
    localStorage.setItem('releaseBranch', releaseBranch)
    set({ sessionId, repoName, releaseBranch })
  },

  setStatus: (status) => set({ status }),
  
  setError: (error) => set({ error }),
  
  clearSession: () => {
    localStorage.removeItem('sessionId')
    localStorage.removeItem('repoName')
    localStorage.removeItem('releaseBranch')
    set({ sessionId: null, repoName: null, releaseBranch: null })
  },
}))
