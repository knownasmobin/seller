const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export function getToken() {
    return localStorage.getItem('adminToken') || ''
}

export function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    }
}

export async function apiFetch(path, options = {}) {
    const res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            ...authHeaders(),
            ...options.headers,
        },
    })

    // If 401, clear token and reload to show login
    if (res.status === 401) {
        localStorage.removeItem('adminToken')
        window.location.reload()
        throw new Error('Session expired')
    }

    return res
}
