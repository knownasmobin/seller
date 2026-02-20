import { useState, useEffect } from 'react'
import { Plus, Trash2, Pencil, X, Check, ToggleLeft, ToggleRight } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export default function Plans() {
    const [plans, setPlans] = useState([])
    const [loading, setLoading] = useState(true)
    const [editingId, setEditingId] = useState(null)
    const [editData, setEditData] = useState({})

    const [showAddForm, setShowAddForm] = useState(false)
    const [newPlan, setNewPlan] = useState({
        server_type: 'v2ray',
        duration_days: 30,
        data_limit_gb: 50,
        price_irr: 0,
        price_usdt: 0,
        is_active: true
    })

    useEffect(() => { fetchPlans() }, [])

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
                setNewPlan({ server_type: 'v2ray', duration_days: 30, data_limit_gb: 50, price_irr: 0, price_usdt: 0, is_active: true })
                fetchPlans()
            }
        } catch (err) {
            console.error("Failed to create plan", err)
        }
    }

    const startEdit = (plan) => {
        setEditingId(plan.ID)
        setEditData({
            duration_days: plan.duration_days,
            data_limit_gb: plan.data_limit_gb,
            price_irr: plan.price_irr,
            price_usdt: plan.price_usdt,
        })
    }

    const cancelEdit = () => {
        setEditingId(null)
        setEditData({})
    }

    const saveEdit = async (id) => {
        try {
            const res = await fetch(`${API_URL}/plans/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editData)
            })
            if (res.ok) {
                setEditingId(null)
                fetchPlans()
            }
        } catch (err) {
            console.error("Failed to update plan", err)
        }
    }

    const toggleActive = async (plan) => {
        try {
            await fetch(`${API_URL}/plans/${plan.ID}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !plan.is_active })
            })
            fetchPlans()
        } catch (err) {
            console.error("Failed to toggle plan", err)
        }
    }

    const deletePlan = async (id) => {
        if (!confirm('Are you sure you want to delete this plan?')) return
        try {
            // We disable it instead of deleting to preserve order history
            await fetch(`${API_URL}/plans/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: false })
            })
            fetchPlans()
        } catch (err) {
            console.error("Failed to delete plan", err)
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
                            <button type="submit" className="btn" style={{ background: 'var(--success)', border: 'none', color: 'white' }}>Save Plan</button>
                        </div>
                    </form>
                </div>
            )}

            <div className="glass" style={{ overflow: 'hidden', animation: 'slideUpFade 0.6s 0.2s both' }}>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Type</th>
                            <th>Duration</th>
                            <th>Data Limit</th>
                            <th>Price (IRR)</th>
                            <th>Price (USDT)</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Loading...</td></tr>
                        ) : plans.length === 0 ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>No plans created yet.</td></tr>
                        ) : (
                            plans.map(plan => (
                                <tr key={plan.ID}>
                                    <td>#{plan.ID}</td>
                                    <td>
                                        <span className={`badge ${plan.server_type === 'v2ray' ? 'badge-primary' : 'badge-warning'}`}>
                                            {plan.server_type.toUpperCase()}
                                        </span>
                                    </td>

                                    {/* Duration */}
                                    <td>
                                        {editingId === plan.ID ? (
                                            <input type="number" className="input-field" style={{ width: '80px', padding: '6px 10px' }}
                                                value={editData.duration_days} onChange={(e) => setEditData({ ...editData, duration_days: parseInt(e.target.value) })} />
                                        ) : (
                                            `${plan.duration_days} Days`
                                        )}
                                    </td>

                                    {/* Data Limit */}
                                    <td>
                                        {editingId === plan.ID ? (
                                            <input type="number" className="input-field" style={{ width: '80px', padding: '6px 10px' }}
                                                value={editData.data_limit_gb} onChange={(e) => setEditData({ ...editData, data_limit_gb: parseInt(e.target.value) })} />
                                        ) : (
                                            `${plan.data_limit_gb} GB`
                                        )}
                                    </td>

                                    {/* Price IRR */}
                                    <td>
                                        {editingId === plan.ID ? (
                                            <input type="number" className="input-field" style={{ width: '120px', padding: '6px 10px' }}
                                                value={editData.price_irr} onChange={(e) => setEditData({ ...editData, price_irr: parseFloat(e.target.value) })} />
                                        ) : (
                                            plan.price_irr.toLocaleString()
                                        )}
                                    </td>

                                    {/* Price USDT */}
                                    <td>
                                        {editingId === plan.ID ? (
                                            <input type="number" step="0.01" className="input-field" style={{ width: '100px', padding: '6px 10px' }}
                                                value={editData.price_usdt} onChange={(e) => setEditData({ ...editData, price_usdt: parseFloat(e.target.value) })} />
                                        ) : (
                                            `$${plan.price_usdt}`
                                        )}
                                    </td>

                                    {/* Status */}
                                    <td>
                                        <button onClick={() => toggleActive(plan)} className="btn" style={{
                                            background: 'transparent', border: 'none', padding: '4px 8px', cursor: 'pointer',
                                            color: plan.is_active ? 'var(--success)' : 'var(--danger)'
                                        }}>
                                            {plan.is_active ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
                                        </button>
                                    </td>

                                    {/* Actions */}
                                    <td>
                                        <div className="flex gap-4" style={{ gap: '8px' }}>
                                            {editingId === plan.ID ? (
                                                <>
                                                    <button onClick={() => saveEdit(plan.ID)} className="btn" style={{ background: 'rgba(16,185,129,0.1)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.2)', padding: '6px 12px' }}>
                                                        <Check size={16} />
                                                    </button>
                                                    <button onClick={cancelEdit} className="btn" style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.2)', padding: '6px 12px' }}>
                                                        <X size={16} />
                                                    </button>
                                                </>
                                            ) : (
                                                <>
                                                    <button onClick={() => startEdit(plan)} className="btn" style={{ background: 'rgba(99,102,241,0.1)', color: 'var(--primary)', border: '1px solid rgba(99,102,241,0.2)', padding: '6px 12px' }}>
                                                        <Pencil size={16} />
                                                    </button>
                                                    <button onClick={() => deletePlan(plan.ID)} className="btn" style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.2)', padding: '6px 12px' }}>
                                                        <Trash2 size={16} />
                                                    </button>
                                                </>
                                            )}
                                        </div>
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
