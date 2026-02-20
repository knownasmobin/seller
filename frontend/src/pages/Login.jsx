import { useState } from 'react'
import { KeyRound, LogIn } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export default function Login({ onLogin }) {
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleLogin = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const res = await fetch(`${API_URL}/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            })

            const data = await res.json()

            if (res.ok && data.token) {
                localStorage.setItem('adminToken', data.token)
                onLogin()
            } else {
                setError(data.error || 'Invalid credentials')
            }
        } catch (err) {
            setError('Unable to connect to backend')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex items-center" style={{ justifyContent: 'center', width: '100%', minHeight: '100vh' }}>
            <div className="glass glass-card" style={{ width: '420px', maxWidth: '90%', animation: 'slideUpFade 0.6s ease both' }}>
                <div className="text-center mb-8">
                    <div style={{ display: 'inline-flex', padding: '18px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '50%', marginBottom: '16px' }}>
                        <KeyRound size={32} color="var(--primary)" />
                    </div>
                    <h2>Admin Login</h2>
                    <p style={{ color: 'var(--text-muted)' }}>Sign in to manage the VPN Sell Bot</p>
                </div>

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div className="input-group" style={{ marginBottom: 0 }}>
                        <label className="input-label">Admin Password</label>
                        <input
                            type="password"
                            className="input-field"
                            placeholder="Enter password..."
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoFocus
                        />
                    </div>

                    {error && (
                        <p style={{ color: 'var(--danger)', fontSize: '0.9rem', margin: 0, padding: '10px 14px', background: 'rgba(239,68,68,0.1)', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.2)' }}>
                            {error}
                        </p>
                    )}

                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', padding: '14px', opacity: loading ? 0.6 : 1 }}>
                        {loading ? (
                            <>
                                <div style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div>
                                Signing in...
                            </>
                        ) : (
                            <>
                                <LogIn size={20} />
                                Access Dashboard
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    )
}
