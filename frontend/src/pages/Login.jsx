import { useState } from 'react'
import { KeyRound, LogIn } from 'lucide-react'

export default function Login({ onLogin }) {
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')

    const handleLogin = (e) => {
        e.preventDefault()
        // For MVP, comparing against a static or env admin password
        // Better: Send a request to /api/v1/auth 
        if (password === 'admin123') { // Placeholder password, ideally read from backend or env
            localStorage.setItem('adminAuth', 'true')
            onLogin()
        } else {
            setError('Invalid admin credentials')
        }
    }

    return (
        <div className="flex items-center justify-center min-h-screen" style={{ width: "100%" }}>
            <div className="glass glass-card" style={{ width: '400px', maxWidth: '90%' }}>
                <div className="text-center mb-8">
                    <div style={{ display: 'inline-flex', padding: '16px', background: 'rgba(79, 70, 229, 0.1)', borderRadius: '50%', marginBottom: '16px' }}>
                        <KeyRound size={32} color="var(--primary)" />
                    </div>
                    <h2>Admin Login</h2>
                    <p style={{ color: 'var(--text-muted)' }}>Sign in to manage the VPN Sell Bot</p>
                </div>

                <form onSubmit={handleLogin} className="flex-col gap-6">
                    <div className="input-group">
                        <label className="input-label">Admin Password</label>
                        <input
                            type="password"
                            className="input-field"
                            placeholder="Enter password..."
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    {error && <p style={{ color: 'var(--danger)', fontSize: '0.875rem', marginBottom: '16px' }}>{error}</p>}

                    <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px' }}>
                        <LogIn size={20} />
                        Access Dashboard
                    </button>
                </form>
            </div>
        </div>
    )
}
