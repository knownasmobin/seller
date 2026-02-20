import { useState, useEffect } from 'react'
import { Activity, Users, ShoppingCart, Server, ArrowUpRight } from 'lucide-react'

export default function Dashboard() {
    const [stats, setStats] = useState({
        users: 0,
        sales: 0,
        activePlans: 0,
        servers: 2
    })

    useEffect(() => {
        setTimeout(() => setStats({ users: 142, sales: 850, activePlans: 5, servers: 2 }), 600)
    }, [])

    return (
        <div className="page container">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1>Overview</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Welcome back, Admin. Here is what is happening today.</p>
                </div>
                <button className="btn btn-primary" style={{ animation: 'slideUpFade 0.6s 0.2s both' }}>
                    <Activity size={18} />
                    View Reports
                </button>
            </div>

            <div className="flex gap-6" style={{ flexWrap: 'wrap' }}>
                <StatCard title="Total Users" value={stats.users} icon={<Users size={24} />} trend="+12% this week" delay={0.1} />
                <StatCard title="Total Orders" value={stats.sales} icon={<ShoppingCart size={24} />} trend="+5% this week" delay={0.2} />
                <StatCard title="Active Plans" value={stats.activePlans} icon={<Server size={24} />} trend="Stable" delay={0.3} />
                <StatCard title="Connected Servers" value={stats.servers} icon={<Activity size={24} />} trend="Online" delay={0.4} />
            </div>

            <div className="mt-8 glass glass-card" style={{ animation: 'slideUpFade 0.6s 0.5s both' }}>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '16px' }}>Recent Activity</h2>
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', borderRadius: '12px' }}>
                    The activity feed will display real-time events from the system here.
                </div>
            </div>
        </div>
    )
}

function StatCard({ title, value, icon, trend, delay }) {
    return (
        <div className="glass glass-card" style={{ flex: '1 1 200px', animation: `slideUpFade 0.6s ${delay}s both` }}>
            <div className="flex justify-between items-center mb-4">
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{title}</h3>
                <span style={{ color: 'var(--primary)', padding: '8px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px' }}>{icon}</span>
            </div>
            <div className="flex items-center gap-4">
                <span style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
                    {typeof value === 'number' ? value.toLocaleString() : value}
                </span>
            </div>
            <div className="mt-4 flex items-center gap-2" style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: 500 }}>
                <ArrowUpRight size={16} />
                {trend}
            </div>
        </div>
    )
}
