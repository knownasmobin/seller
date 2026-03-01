import { useState, useEffect } from 'react'
import { Plus, Save, Trash2, Edit2, CheckCircle, AlertCircle, Globe, Shield } from 'lucide-react'
import { apiFetch } from '../api'

export default function Endpoints() {
    const [endpoints, setEndpoints] = useState([])
    const [allowedApps, setAllowedApps] = useState('')
    const [loading, setLoading] = useState(true)
    const [editingEndpoint, setEditingEndpoint] = useState(null)
    const [editData, setEditData] = useState({})
    const [isCreating, setIsCreating] = useState(false)
    const [savingAllowedApps, setSavingAllowedApps] = useState(false)
    const [toast, setToast] = useState(null)

    useEffect(() => {
        fetchWireGuardDashboard()
    }, [])

    const showToast = (success, message) => {
        setToast({ success, message })
        setTimeout(() => setToast(null), 3000)
    }

    const fetchWireGuardDashboard = async () => {
        try {
            const res = await apiFetch('/admin/wireguard')
            if (res.ok) {
                const data = await res.json()
                setEndpoints(data.endpoints || [])
                setAllowedApps(data.wiresock_allowed_apps || '')
            }
        } catch {
            console.error('Failed to fetch WireGuard dashboard data')
        } finally {
            setLoading(false)
        }
    }

    const saveAllowedAppsConfig = async () => {
        setSavingAllowedApps(true)
        try {
            const res = await apiFetch('/admin/wireguard', {
                method: 'PATCH',
                body: JSON.stringify({ wiresock_allowed_apps: allowedApps })
            })

            if (res.ok) {
                showToast(true, 'WireSock allowed apps updated successfully')
            } else {
                showToast(false, 'Failed to update WireSock allowed apps')
            }
        } catch {
            showToast(false, 'Connection error')
        } finally {
            setSavingAllowedApps(false)
        }
    }

    const startEdit = (ep) => {
        setEditingEndpoint(ep.ID)
        setEditData({
            name: ep.name,
            address: ep.address,
            is_active: ep.is_active
        })
    }

    const startCreate = () => {
        setIsCreating(true)
        setEditData({
            name: '',
            address: '',
            is_active: true
        })
    }

    const saveEdit = async (id) => {
        try {
            const res = await apiFetch(`/endpoints/${id}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    name: editData.name,
                    address: editData.address,
                    is_active: editData.is_active
                })
            })
            if (res.ok) {
                setEditingEndpoint(null)
                fetchWireGuardDashboard()
                showToast(true, 'Endpoint updated successfully')
            } else {
                showToast(false, 'Failed to update endpoint')
            }
        } catch {
            showToast(false, 'Connection error')
        }
    }

    const saveCreate = async () => {
        try {
            const res = await apiFetch('/endpoints', {
                method: 'POST',
                body: JSON.stringify({
                    name: editData.name,
                    address: editData.address,
                    is_active: editData.is_active
                })
            })
            if (res.ok) {
                setIsCreating(false)
                fetchWireGuardDashboard()
                showToast(true, 'Endpoint created successfully')
            } else {
                showToast(false, 'Failed to create endpoint')
            }
        } catch {
            showToast(false, 'Connection error')
        }
    }

    const deleteEndpoint = async (id) => {
        if (!window.confirm('Are you sure you want to delete this endpoint?')) return

        try {
            const res = await apiFetch(`/endpoints/${id}`, {
                method: 'DELETE'
            })
            if (res.ok) {
                fetchWireGuardDashboard()
                showToast(true, 'Endpoint deleted')
            } else {
                showToast(false, 'Failed to delete endpoint')
            }
        } catch {
            showToast(false, 'Connection error')
        }
    }

    if (loading) {
        return (
            <div className="page container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ width: 40, height: 40, border: '3px solid var(--glass-border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }}></div>
                    Loading WireGuard dashboard...
                </div>
            </div>
        )
    }

    return (
        <div className="page container">
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
                <h1>WireGuard Dashboard</h1>
                <p style={{ color: 'var(--text-muted)' }}>Manage WireSock application policy and WireGuard endpoints</p>
            </div>

            <div className="glass glass-card mb-8" style={{ animation: 'slideUpFade 0.4s ease both' }}>
                <div className="flex items-center gap-4 mb-6">
                    <span style={{ padding: '10px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '10px', color: 'var(--primary)' }}>
                        <Shield size={22} />
                    </span>
                    <div>
                        <h3 style={{ margin: 0 }}>WireSock Allowed Apps</h3>
                        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Applied to generated WireGuard configs at runtime.
                        </p>
                    </div>
                </div>
                <div className="input-group" style={{ marginBottom: '16px' }}>
                    <label htmlFor="allowed-apps-textarea" className="input-label">Allowed apps list (pass-through format)</label>
                    <textarea
                        id="allowed-apps-textarea"
                        className="input-field"
                        value={allowedApps}
                        onChange={(e) => setAllowedApps(e.target.value)}
                        rows={4}
                        placeholder="Example: chrome.exe,firefox.exe,telegram.exe"
                        style={{ resize: 'vertical' }}
                    />
                </div>
                <div className="flex gap-4">
                    <button className="btn btn-primary" onClick={saveAllowedAppsConfig} disabled={savingAllowedApps}>
                        <Save size={16} /> {savingAllowedApps ? 'Saving...' : 'Save Allowed Apps'}
                    </button>
                </div>
            </div>

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 style={{ marginBottom: '6px' }}>WireGuard Endpoints</h2>
                    <p style={{ color: 'var(--text-muted)' }}>Manage remote endpoint options users can pick</p>
                </div>
                {!isCreating && (
                    <button className="btn btn-primary" onClick={startCreate}>
                        <Plus size={18} />
                        Add Endpoint
                    </button>
                )}
            </div>

            <div className="flex flex-col gap-6">
                {isCreating && (
                    <div className="glass glass-card" style={{ animation: 'slideUpFade 0.4s ease both' }}>
                        <div className="flex items-center gap-4 mb-6">
                            <span style={{ padding: '10px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '10px', color: 'var(--primary)' }}>
                                <Globe size={22} />
                            </span>
                            <h3>New Endpoint</h3>
                        </div>
                        <div className="flex gap-6 mb-6" style={{ flexWrap: 'wrap' }}>
                            <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                                <label htmlFor="endpoint-name-create" className="input-label">Name (e.g. 🇩🇪 Germany)</label>
                                <input id="endpoint-name-create" type="text" className="input-field" value={editData.name}
                                    placeholder="Germany"
                                    onChange={(e) => setEditData({ ...editData, name: e.target.value })} />
                            </div>
                            <div className="input-group" style={{ flex: '1 1 300px', marginBottom: 0 }}>
                                <label htmlFor="endpoint-address-create" className="input-label">Address (host:port)</label>
                                <input id="endpoint-address-create" type="text" className="input-field" value={editData.address}
                                    placeholder="de.example.com:51820"
                                    onChange={(e) => setEditData({ ...editData, address: e.target.value })} />
                            </div>
                            <div className="input-group" style={{ flex: '0 0 auto', marginBottom: 0 }}>
                                <label className="input-label">Status</label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderRadius: '10px' }}>
                                    <input type="checkbox" checked={editData.is_active}
                                        onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })}
                                        style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }} />
                                    Active
                                </label>
                            </div>
                        </div>
                        <div className="flex gap-4">
                            <button className="btn" style={{ background: 'var(--success)', color: 'white', border: 'none' }} onClick={saveCreate}>
                                <Save size={16} /> Save Endpoint
                            </button>
                            <button className="btn btn-ghost" onClick={() => setIsCreating(false)}>Cancel</button>
                        </div>
                    </div>
                )}

                {endpoints.map((ep, idx) => {
                    const isEditing = editingEndpoint === ep.ID
                    return (
                        <div key={ep.ID} className="glass glass-card flex-col" style={{ animation: `slideUpFade 0.6s ${0.1 + idx * 0.1}s both` }}>
                            {isEditing ? (
                                <div className="flex flex-col gap-6">
                                    <div className="flex items-center gap-4">
                                        <span style={{ padding: '10px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '10px', color: 'var(--primary)' }}>
                                            <Globe size={22} />
                                        </span>
                                        <h3 style={{ margin: 0 }}>Edit {ep.name}</h3>
                                    </div>
                                    <div className="flex gap-6" style={{ flexWrap: 'wrap' }}>
                                        <div className="input-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
                                            <label htmlFor={`endpoint-name-edit-${ep.ID}`} className="input-label">Name</label>
                                            <input id={`endpoint-name-edit-${ep.ID}`} type="text" className="input-field" value={editData.name}
                                                onChange={(e) => setEditData({ ...editData, name: e.target.value })} />
                                        </div>
                                        <div className="input-group" style={{ flex: '1 1 300px', marginBottom: 0 }}>
                                            <label htmlFor={`endpoint-address-edit-${ep.ID}`} className="input-label">Address (host:port)</label>
                                            <input id={`endpoint-address-edit-${ep.ID}`} type="text" className="input-field" value={editData.address}
                                                onChange={(e) => setEditData({ ...editData, address: e.target.value })} />
                                        </div>
                                        <div className="input-group" style={{ flex: '0 0 auto', marginBottom: 0 }}>
                                            <label className="input-label">Status</label>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderRadius: '10px' }}>
                                                <input type="checkbox" checked={editData.is_active}
                                                    onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })}
                                                    style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }} />
                                                Active
                                            </label>
                                        </div>
                                    </div>
                                    <div className="flex gap-4">
                                        <button className="btn" style={{ background: 'var(--success)', color: 'white', border: 'none' }} onClick={() => saveEdit(ep.ID)}>
                                            <Save size={16} /> Save Changes
                                        </button>
                                        <button className="btn btn-ghost" onClick={() => setEditingEndpoint(null)}>Cancel</button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex justify-between items-center w-100">
                                    <div className="flex items-center gap-6">
                                        <span style={{ padding: '12px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '12px', color: 'var(--primary)' }}>
                                            <Globe size={24} />
                                        </span>
                                        <div>
                                            <h3 style={{ margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                {ep.name}
                                                {!ep.is_active && (
                                                    <span className="badge badge-error" style={{ fontSize: '0.7rem' }}>Inactive</span>
                                                )}
                                            </h3>
                                            <div style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '0.9rem', background: 'rgba(0,0,0,0.2)', padding: '4px 8px', borderRadius: '6px', display: 'inline-block' }}>
                                                {ep.address}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-4">
                                        <button className="btn btn-ghost" onClick={() => startEdit(ep)} style={{ color: 'var(--primary)' }} aria-label="Edit endpoint">
                                            <Edit2 size={18} />
                                        </button>
                                        <button className="btn btn-ghost" onClick={() => deleteEndpoint(ep.ID)} style={{ color: 'var(--danger)' }} aria-label="Delete endpoint">
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )
                })}

                {endpoints.length === 0 && !isCreating && !loading && (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
                        <Globe size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
                        <p>No endpoints configured yet.</p>
                    </div>
                )}
            </div>
        </div>
    )
}
