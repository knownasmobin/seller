import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Save, Server, CreditCard, Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react'
import { apiFetch } from '../api'

export default function Settings() {
    const [servers, setServers] = useState([])
    const [settings, setSettings] = useState({})
    const [loading, setLoading] = useState(true)
    const [editingServer, setEditingServer] = useState(null)
    const [editData, setEditData] = useState({})
    const [showPasswords, setShowPasswords] = useState({})
    const [cardNumber, setCardNumber] = useState('')
    const [toast, setToast] = useState(null)

    useEffect(() => {
        fetchAll()
    }, [])

    const fetchAll = async () => {
        try {
            const [serversRes, settingsRes] = await Promise.all([
                apiFetch('/admin/servers'),
                apiFetch('/admin/settings')
            ])
            if (serversRes.ok) {
                const data = await serversRes.json()
                setServers(data || [])
            }
            if (settingsRes.ok) {
                const data = await settingsRes.json()
                setSettings(data)
                setCardNumber(data.admin_card_number || '')
            }
        } catch (err) {
            console.error("Failed to fetch settings", err)
        } finally {
            setLoading(false)
        }
    }

    const showToast = (success, message) => {
        setToast({ success, message })
        setTimeout(() => setToast(null), 3000)
    }

    const startEditServer = (server) => {
        let creds = { username: '', password: '' }
        try { creds = JSON.parse(server.credentials || '{}') } catch (e) { }
        setEditingServer(server.ID)
        setEditData({
            name: server.name,
            api_url: server.api_url,
            username: creds.username || '',
            password: creds.password || '',
        })
    }

    const saveServer = async (id) => {
        try {
            const payload = {
                name: editData.name,
                api_url: editData.api_url,
                credentials: JSON.stringify({ username: editData.username, password: editData.password })
            }
            const res = await apiFetch(`/admin/servers/${id}`, {
                method: 'PATCH',
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setEditingServer(null)
                fetchAll()
                showToast(true, 'Server updated successfully')
            } else {
                showToast(false, 'Failed to update server')
            }
        } catch (err) {
            showToast(false, 'Connection error')
        }
    }

    const saveCardNumber = async () => {
        try {
            const res = await apiFetch('/admin/settings', {
                method: 'PATCH',
                body: JSON.stringify({ admin_card_number: cardNumber })
            })
            if (res.ok) {
                showToast(true, 'Card number updated')
            } else {
                showToast(false, 'Failed to update card number')
            }
        } catch (err) {
            showToast(false, 'Connection error')
        }
    }

    const togglePassword = (id) => {
        setShowPasswords(prev => ({ ...prev, [id]: !prev[id] }))
    }

    const parseCredentials = (credStr) => {
        try { return JSON.parse(credStr || '{}') } catch { return {} }
    }

    if (loading) {
        return (
            <div className="page container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ width: 40, height: 40, border: '3px solid var(--glass-border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }}></div>
                    Loading settings...
                </div>
            </div>
        )
    }

    return (
        <div className="page container">
            {/* Toast Notification */}
            {toast && (
                <div style={{
                    position: 'fixed', top: 24, right: 24, zIndex: 1000,
                    padding: '14px 24px', borderRadius: '12px',
                    background: toast.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    border: `1px solid ${toast.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                    backdropFilter: 'blur(12px)',
                    color: toast.success ? 'var(--success)' : 'var(--danger)',
                    display: 'flex', alignItems: 'center', gap: '10px',
                    animation: 'slideUpFade 0.4s ease both',
                    fontWeight: 600
                }}>
                    {toast.success ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                    {toast.message}
                </div>
            )}

            <div className="mb-8">
                <h1>Settings</h1>
                <p style={{ color: 'var(--text-muted)' }}>Manage VPN server connections and payment configuration</p>
            </div>

            {/* Card Number */}
            <div className="glass glass-card mb-8" style={{ animation: 'slideUpFade 0.6s 0.1s both' }}>
                <div className="flex items-center gap-4" style={{ marginBottom: '20px' }}>
                    <span style={{ padding: '10px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '10px', color: 'var(--warning)' }}>
                        <CreditCard size={22} />
                    </span>
                    <div>
                        <h3 style={{ margin: 0 }}>Payment Card Number</h3>
                        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.85rem' }}>The card number shown to users for bank transfer payments</p>
                    </div>
                </div>
                <div className="flex gap-4 items-center">
                    <input
                        type="text"
                        className="input-field"
                        value={cardNumber}
                        onChange={(e) => setCardNumber(e.target.value)}
                        placeholder="1234-5678-9012-3456"
                        style={{ flex: 1, marginBottom: 0 }}
                    />
                    <button className="btn btn-primary" onClick={saveCardNumber} style={{ height: '50px' }}>
                        <Save size={18} />
                        Save
                    </button>
                </div>
            </div>

            {/* Servers */}
            <div style={{ animation: 'slideUpFade 0.6s 0.2s both' }}>
                <div className="flex items-center gap-4 mb-8">
                    <span style={{ padding: '10px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '10px', color: 'var(--primary)' }}>
                        <Server size={22} />
                    </span>
                    <div>
                        <h2 style={{ margin: 0 }}>VPN Servers</h2>
                        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.85rem' }}>Marzban and WireGuard panel connections</p>
                    </div>
                </div>

                <div className="flex flex-col gap-6">
                    {servers.map((server, idx) => {
                        const creds = parseCredentials(server.credentials)
                        const isEditing = editingServer === server.ID
                        const typeBadge = server.server_type === 'v2ray' ? 'badge-primary' : 'badge-warning'

                        return (
                            <div key={server.ID} className="glass glass-card" style={{ animation: `slideUpFade 0.6s ${0.3 + idx * 0.1}s both` }}>
                                <div className="flex justify-between items-center" style={{ marginBottom: '20px' }}>
                                    <div className="flex items-center gap-4">
                                        <span className={`badge ${typeBadge}`}>{server.server_type?.toUpperCase()}</span>
                                        <h3 style={{ margin: 0 }}>{server.name}</h3>
                                    </div>
                                    {!isEditing ? (
                                        <button className="btn btn-ghost" onClick={() => startEditServer(server)}>Edit</button>
                                    ) : (
                                        <div className="flex gap-4">
                                            <button className="btn" style={{ background: 'var(--success)', color: 'white', border: 'none' }} onClick={() => saveServer(server.ID)}>
                                                <Save size={16} /> Save
                                            </button>
                                            <button className="btn btn-ghost" onClick={() => setEditingServer(null)}>Cancel</button>
                                        </div>
                                    )}
                                </div>

                                <div className="flex gap-6" style={{ flexWrap: 'wrap' }}>
                                    <div className="input-group" style={{ flex: '1 1 300px', marginBottom: 0 }}>
                                        <label className="input-label">Panel URL</label>
                                        {isEditing ? (
                                            <input type="text" className="input-field" value={editData.api_url}
                                                onChange={(e) => setEditData({ ...editData, api_url: e.target.value })} />
                                        ) : (
                                            <div style={{ padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderRadius: '10px', fontFamily: 'monospace', fontSize: '0.9rem', wordBreak: 'break-all' }}>
                                                {server.api_url}
                                            </div>
                                        )}
                                    </div>
                                    <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                                        <label className="input-label">Username</label>
                                        {isEditing ? (
                                            <input type="text" className="input-field" value={editData.username}
                                                onChange={(e) => setEditData({ ...editData, username: e.target.value })} />
                                        ) : (
                                            <div style={{ padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderRadius: '10px', fontSize: '0.9rem' }}>
                                                {creds.username || '—'}
                                            </div>
                                        )}
                                    </div>
                                    <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                                        <label className="input-label">Password</label>
                                        {isEditing ? (
                                            <div style={{ position: 'relative' }}>
                                                <input type={showPasswords[server.ID] ? 'text' : 'password'} className="input-field" value={editData.password}
                                                    onChange={(e) => setEditData({ ...editData, password: e.target.value })}
                                                    style={{ paddingRight: '44px' }} />
                                                <button onClick={() => togglePassword(server.ID)} style={{
                                                    position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
                                                    background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
                                                }}>
                                                    {showPasswords[server.ID] ? <EyeOff size={18} /> : <Eye size={18} />}
                                                </button>
                                            </div>
                                        ) : (
                                            <div style={{ padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderRadius: '10px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                <span>{showPasswords[server.ID] ? (creds.password || '—') : '••••••••'}</span>
                                                <button onClick={() => togglePassword(server.ID)} style={{
                                                    background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0
                                                }}>
                                                    {showPasswords[server.ID] ? <EyeOff size={16} /> : <Eye size={16} />}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
