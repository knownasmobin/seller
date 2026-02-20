import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1'

export default function Orders() {
    const [orders, setOrders] = useState([])
    const [loading, setLoading] = useState(true)
    const [searchId, setSearchId] = useState('')

    // Placeholder for fetching all orders. The backend currently only has GetUserOrders
    // If an Admin GetAllOrders endpoint is created, point it there. 
    // For now, we will handle a simple search by telegram ID

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!searchId) return

        setLoading(true)
        try {
            const res = await fetch(`${API_URL}/users/${searchId}/orders`)
            if (res.ok) {
                const data = await res.json()
                setOrders(data || [])
            } else {
                setOrders([])
            }
        } catch (err) {
            console.error("Fetch orders failed", err)
            setOrders([])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="page" style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2>Orders & Subscriptions</h2>
                    <p style={{ color: 'var(--text-muted)' }}>Lookup user orders by Telegram ID</p>
                </div>
            </div>

            <div className="glass glass-card mb-8">
                <form onSubmit={handleSearch} className="flex gap-4 items-center">
                    <div className="input-group" style={{ margin: 0, flex: 1 }}>
                        <input
                            type="text"
                            className="input-field"
                            placeholder="Search by Telegram User ID (e.g., 123456789)..."
                            value={searchId}
                            onChange={(e) => setSearchId(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ height: '44px' }}>Lookup User</button>
                </form>
            </div>

            <div className="glass" style={{ overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', borderBottom: '1px solid var(--glass-border)' }}>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Order ID</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Plan ID</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Amount</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Payment Method</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Date</th>
                            <th style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading && !searchId ? (
                            <tr><td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>Enter a Telegram ID to search</td></tr>
                        ) : loading ? (
                            <tr><td colSpan="6" style={{ padding: '24px', textAlign: 'center' }}>Loading...</td></tr>
                        ) : orders.length === 0 ? (
                            <tr><td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No orders found for this user.</td></tr>
                        ) : (
                            orders.map(order => (
                                <tr key={order.ID} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                                    <td style={{ padding: '16px 24px' }}>#{order.ID}</td>
                                    <td style={{ padding: '16px 24px' }}>Plan #{order.plan_id}</td>
                                    <td style={{ padding: '16px 24px' }}>{order.amount.toLocaleString()}</td>
                                    <td style={{ padding: '16px 24px', textTransform: 'capitalize' }}>{order.payment_method}</td>
                                    <td style={{ padding: '16px 24px' }}>{new Date(order.CreatedAt).toLocaleDateString()}</td>
                                    <td style={{ padding: '16px 24px' }}>
                                        <span className={`badge ${order.payment_status === 'paid' ? 'badge-success' : 'badge-warning'}`}>
                                            {order.payment_status.toUpperCase()}
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
