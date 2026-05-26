import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Session APIs
export const sessionAPI = {
  create: (repoName: string, releaseBranch: string) =>
    apiClient.post('/sessions', { repo_name: repoName, release_branch: releaseBranch }),
  get: (sessionId: string) => apiClient.get(`/sessions/${sessionId}`),
  list: () => apiClient.get('/sessions'),
  delete: (sessionId: string) => apiClient.delete(`/sessions/${sessionId}`),
}

// Analysis APIs
export const analysisAPI = {
  quickAnalyze: (sessionId: string) => apiClient.post(`/sessions/${sessionId}/quick-analyze`),
  deepAnalyze: (sessionId: string) => apiClient.post(`/sessions/${sessionId}/analyze`, { deep: true }),
}

// Chat APIs
export const chatAPI = {
  sendMessage: (sessionId: string, content: string) =>
    apiClient.post(`/sessions/${sessionId}/chat`, { content }),
  getHistory: (sessionId: string) => apiClient.get(`/sessions/${sessionId}/chat`),
  getAIResponse: (sessionId: string, content: string) =>
    apiClient.post(`/sessions/${sessionId}/ai-response`, { content }),
}

// CI APIs
export const ciAPI = {
  generateCI: (sessionId: string, requirements: string) =>
    apiClient.post(`/sessions/${sessionId}/generate-ci`, { requirements }),
  createPR: (sessionId: string, ciId: string) =>
    apiClient.post(`/sessions/${sessionId}/ci/${ciId}/create-pr`),
  getPRStatus: (sessionId: string, ciId: string) =>
    apiClient.get(`/sessions/${sessionId}/ci/${ciId}/pr-status`),
  getPRDiff: (sessionId: string, ciId: string) =>
    apiClient.get(`/sessions/${sessionId}/ci/${ciId}/pr-diff`),
  approveGitHub: (sessionId: string, ciId: string) =>
    apiClient.post(`/sessions/${sessionId}/ci/${ciId}/approve-github`),
  approveChat: (sessionId: string, ciId: string) =>
    apiClient.post(`/sessions/${sessionId}/ci/${ciId}/approve-chat`),
}
