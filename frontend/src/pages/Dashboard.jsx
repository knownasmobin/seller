import { useState, useEffect } from 'react'
import { Activity, Users, ShoppingCart, Server, ArrowUpRight, DollarSign, Clock } from 'lucide-react'
import { apiFetch } from '../api'

export default function Dashboard() {
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchStats()
    }, [])

    const fetchStats = async () => {
        try {
            const res = await apiFetch('/admin/stats')
            if (res.ok) {
                const data = await res.json()
                setStats(data)
            }
        } catch (err) {
            console.error("Failed to fetch stats", err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="page container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div className="spinner" style={{ width: 40, height: 40, border: '3px solid var(--glass-border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }}></div>
                    Loading dashboard...
                </div>
            </div>
        )
    }

    const s = stats || {}

    return (
        <div className="page container">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1>Overview</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Welcome back, Admin. Here is what is happening.</p>
                </div>
            </div>

            <div className="flex gap-6" style={{ flexWrap: 'wrap' }}>
                <StatCard title="Total Users" value={s.total_users || 0} icon={<Users size={22} />} color="var(--primary)" delay={0.1} />
                <StatCard title="Total Orders" value={s.total_orders || 0} icon={<ShoppingCart size={22} />} color="var(--warning)" delay={0.2} />
                <StatCard title="Active Plans" value={s.active_plans || 0} icon={<Server size={22} />} color="var(--success)" delay={0.3} />
                <StatCard title="Active Subs" value={s.active_subscriptions || 0} icon={<Activity size={22} />} color="#8b5cf6" delay={0.4} />
            </div>

            {/* Revenue Cards */}
            <div className="flex gap-6 mt-8" style={{ flexWrap: 'wrap' }}>
                <div className="glass glass-card" style={{ flex: '1 1 300px', animation: 'slideUpFade 0.6s 0.5s both' }}>
                    <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Revenue (IRR)</h3>
                        <span style={{ color: 'var(--success)', padding: '8px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px' }}><DollarSign size={20} /></span>
                    </div>
                    <span style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                        {(s.total_revenue_irr || 0).toLocaleString()}
                    </span>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>{s.paid_orders || 0} paid orders</p>
                </div>
                <div className="glass glass-card" style={{ flex: '1 1 300px', animation: 'slideUpFade 0.6s 0.6s both' }}>
                    <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Revenue (USDT)</h3>
                        <span style={{ color: 'var(--warning)', padding: '8px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '8px' }}><DollarSign size={20} /></span>
                    </div>
                    <span style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                        ${(s.total_revenue_usdt || 0).toFixed(2)}
                    </span>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>{s.pending_orders || 0} pending orders</p>
                </div>
            </div>

            {/* Recent Orders */}
            <div className="mt-8 glass" style={{ overflow: 'hidden', animation: 'slideUpFade 0.6s 0.7s both' }}>
                <div style={{ padding: '24px 28px 16px' }}>
                    <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Recent Orders</h2>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Order</th>
                            <th>Telegram ID</th>
                            <th>Plan</th>
                            <th>Amount</th>
                            <th>Method</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(!s.recent_orders || s.recent_orders.length === 0) ? (
                            <tr>
                                <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                                    No orders yet.
                                </td>
                            </tr>
                        ) : (
                            s.recent_orders.map(order => (
                                <tr key={order.id}>
                                    <td>#{order.id}</td>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{order.telegram_id}</td>
                                    <td>Plan #{order.plan_id}</td>
                                    <td>{order.amount?.toLocaleString()}</td>
                                    <td><span className={`badge ${order.payment_method === 'crypto' ? 'badge-warning' : 'badge-primary'}`}>{(order.payment_method || '').toUpperCase()}</span></td>
                                    <td><span className={`badge ${order.payment_status === 'paid' ? 'badge-success' : order.payment_status === 'pending' ? 'badge-warning' : 'badge-danger'}`}>{(order.payment_status || '').toUpperCase()}</span></td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{order.created_at ? new Date(order.created_at).toLocaleString() : '-'}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

function StatCard({ title, value, icon, color, delay }) {
    return (
        <div className="glass glass-card" style={{ flex: '1 1 200px', animation: `slideUpFade 0.6s ${delay}s both` }}>
            <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{title}</h3>
                <span style={{ color: color, padding: '8px', background: `${color}15`, borderRadius: '8px' }}>{icon}</span>
            </div>
            <div>
                <span style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                    {typeof value === 'number' ? value.toLocaleString() : value}
                </span>
            </div>
        </div>
    )
}
