import { useState, useEffect } from 'react'
import { Plus, Trash2 } from 'lucide-react'

// Adjust this URL to point to your Go Backend if not served on the same domain
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1'

export default function Plans() {
    const [plans, setPlans] = useState([])
    const [loading, setLoading] = useState(true)

    // New Plan Form State
    const [showAddForm, setShowAddForm] = useState(false)
    const [newPlan, setNewPlan] = useState({
        server_type: 'v2ray',
        duration_days: 30,
        data_limit_gb: 50,
        price_irr: 0,
        price_usdt: 0,
        is_active: true
    })

    useEffect(() => {
        fetchPlans()
    }, [])

    const fetchPlans = async () => {
        try {
            const res = await fetch(`${API_URL}/plans`)
            const data = await res.json()
            setPlans(data || [])
        } catch (err) {
            console.error("Failed to fetch plans", err)
        } finally {
            setLoading(false)
        }
    }

    const handleCreatePlan = async (e) => {
        e.preventDefault()
        try {
            const res = await fetch(`${API_URL}/plans`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newPlan)
            })
            if (res.ok) {
                setShowAddForm(false)
                fetchPlans()
            }
        } catch (err) {
            console.error("Failed to create plan", err)
        }
    }

    return (
        <div className="page container">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1>VPN Plans</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Manage your available V2Ray and WireGuard subscription plans</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
                    <Plus size={18} />
                    {showAddForm ? 'Cancel' : 'Add New Plan'}
                </button>
            </div>

            {showAddForm && (
                <div className="glass glass-card mb-8" style={{ animation: 'slideUpFade 0.5s ease both' }}>
                    <h3 style={{ marginBottom: '16px' }}>Create New Plan</h3>
                    <form onSubmit={handleCreatePlan} className="flex gap-4" style={{ flexWrap: 'wrap' }}>
                        <div className="input-group" style={{ flex: '1 1 150px' }}>
                            <label className="input-label">Type</label>
                            <select className="input-field" value={newPlan.server_type} onChange={(e) => setNewPlan({ ...newPlan, server_type: e.target.value })}>
                                <option value="v2ray">V2Ray</option>
                                <option value="wireguard">WireGuard</option>
                            </select>
                        </div>
                        <div className="input-group" style={{ flex: '1 1 150px' }}>
                            <label className="input-label">Days</label>
                            <input type="number" className="input-field" value={newPlan.duration_days} onChange={(e) => setNewPlan({ ...newPlan, duration_days: parseInt(e.target.value) })} />
                        </div>
                        <div className="input-group" style={{ flex: '1 1 150px' }}>
                            <label className="input-label">Data (GB)</label>
                            <input type="number" className="input-field" value={newPlan.data_limit_gb} onChange={(e) => setNewPlan({ ...newPlan, data_limit_gb: parseInt(e.target.value) })} />
                        </div>
                        <div className="input-group" style={{ flex: '1 1 150px' }}>
                            <label className="input-label">Price (IRR)</label>
                            <input type="number" className="input-field" value={newPlan.price_irr} onChange={(e) => setNewPlan({ ...newPlan, price_irr: parseFloat(e.target.value) })} />
                        </div>
                        <div className="input-group" style={{ flex: '1 1 150px' }}>
                            <label className="input-label">Price (USDT)</label>
                            <input type="number" step="0.01" className="input-field" value={newPlan.price_usdt} onChange={(e) => setNewPlan({ ...newPlan, price_usdt: parseFloat(e.target.value) })} />
                        </div>
                        <div className="flex items-center" style={{ width: '100%', marginTop: '16px' }}>
                            <button type="submit" className="btn btn-success" style={{ background: 'var(--success)', border: 'none', color: 'white' }}>Save Plan</button>
                        </div>
                    </form>
                </div>
            )}

            <div className="glass" style={{ overflow: 'hidden', animation: 'slideUpFade 0.6s 0.2s both' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', borderBottom: '1px solid var(--glass-border)' }}>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>ID</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Type</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Duration</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Data Limit</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Price</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="6" style={{ padding: '24px', textAlign: 'center' }}>Loading...</td></tr>
                        ) : plans.length === 0 ? (
                            <tr><td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No plans created yet.</td></tr>
                        ) : (
                            plans.map(plan => (
                                <tr key={plan.ID} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                                    <td style={{ padding: '16px 24px' }}>#{plan.ID}</td>
                                    <td style={{ padding: '16px 24px' }}>
                                        <span className={plan.server_type === 'v2ray' ? 'badge badge-primary' : 'badge badge-warning'} style={{
                                            background: plan.server_type === 'v2ray' ? 'rgba(79, 70, 229, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                                            color: plan.server_type === 'v2ray' ? 'var(--primary)' : 'var(--warning)',
                                            border: plan.server_type === 'v2ray' ? '1px solid rgba(79, 70, 229, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)'
                                        }}>
                                            {plan.server_type.toUpperCase()}
                                        </span>
                                    </td>
                                    <td style={{ padding: '16px 24px' }}>{plan.duration_days} Days</td>
                                    <td style={{ padding: '16px 24px' }}>{plan.data_limit_gb} GB</td>
                                    <td style={{ padding: '16px 24px' }}>{plan.price_irr.toLocaleString()} IRR / ${plan.price_usdt}</td>
                                    <td style={{ padding: '16px 24px' }}>
                                        <span className={plan.is_active ? 'badge badge-success' : 'badge badge-danger'}>
                                            {plan.is_active ? 'Active' : 'Disabled'}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
