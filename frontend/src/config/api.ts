// API Configuration for different environments
// In Docker, Nginx proxies /inventory/* to the backend

const isDev = import.meta.env.DEV;

export const API_BASE_URL = isDev
    ? 'http://localhost:8000'  // Development: direct to backend
    : '';                       // Production: relative URL (Nginx proxy)

export const API_ENDPOINTS = {
    uploadMask: `${API_BASE_URL}/inventory/upload-mask`,
    downloadTemplate: (sessionId: number) => `${API_BASE_URL}/inventory/download-template/${sessionId}`,
    uploadFilledTemplate: (sessionId: number) => `${API_BASE_URL}/inventory/upload-filled-template/${sessionId}`,
    downloadFile: (sessionId: number, fileType: string) => `${API_BASE_URL}/inventory/download-file/${sessionId}/${fileType}`,
    activeSessions: `${API_BASE_URL}/inventory/active-sessions`,
    resumeSession: (sessionId: number) => `${API_BASE_URL}/inventory/session/${sessionId}/resume`,
    deleteSession: (sessionId: number) => `${API_BASE_URL}/inventory/session/${sessionId}`,
};
