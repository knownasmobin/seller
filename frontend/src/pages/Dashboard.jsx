import { useState, useEffect } from 'react'
import { Activity, Users, ShoppingCart, Server, ArrowUpRight } from 'lucide-react'

export default function Dashboard() {
    const [stats, setStats] = useState({
        users: 0,
        sales: 0,
        activePlans: 0,
        servers: 2 // Marzban, WgPortal
    })

    // Mock fetching stats - later hook this to actual /api/v1 endpoints if you build summary routes
    useEffect(() => {
        // Simulating API fetch
        setTimeout(() => setStats({ users: 142, sales: 850, activePlans: 5, servers: 2 }), 1000)
    }, [])

    return (
        <div className="page" style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 style={{ color: 'var(--text-main)', marginBottom: '8px' }}>Overview</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Welcome back, Admin. Here is what is happening today.</p>
                </div>
                <button className="btn btn-primary">
                    <Activity size={18} />
                    View Reports
                </button>
            </div>

            <div className="flex gap-6" style={{ flexWrap: 'wrap' }}>
                <StatCard title="Total Users" value={stats.users} icon={<Users size={24} />} trend="+12% this week" />
                <StatCard title="Total Orders" value={stats.sales} icon={<ShoppingCart size={24} />} trend="+5% this week" />
                <StatCard title="Active Plans" value={stats.activePlans} icon={<Server size={24} />} trend="Stable" />
                <StatCard title="Connected Servers" value={stats.servers} icon={<Activity size={24} />} trend="Online" />
            </div>

            <div className="mt-8 glass glass-card">
                <h2 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>Recent Activity</h2>
                <p style={{ color: 'var(--text-muted)' }}>The activity feed will display real-time events from the system here.</p>
            </div>
        </div>
    )
}

function StatCard({ title, value, icon, trend }) {
    return (
        <div className="glass glass-card" style={{ flex: '1 1 200px' }}>
            <div className="flex justify-between items-center mb-4">
                <h3 style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)', margin: 0 }}>{title}</h3>
                <span style={{ color: 'var(--primary)' }}>{icon}</span>
            </div>
            <div className="flex items-center gap-4">
                <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-main)' }}>{value}</span>
            </div>
            <div className="mt-4 flex items-center gap-2" style={{ fontSize: '0.75rem', color: 'var(--success)' }}>
                <ArrowUpRight size={14} />
                {trend}
            </div>
        </div>
    )
}
