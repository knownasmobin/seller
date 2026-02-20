import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Server, Users, LogOut } from 'lucide-react';

export default function Sidebar({ onLogout }) {
    const navItems = [
        { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
        { name: 'Active Plans', path: '/plans', icon: <Server size={20} /> },
        { name: 'User Orders', path: '/orders', icon: <Users size={20} /> },
    ];

    return (
        <aside className="glass" style={{ width: '260px', borderRadius: 0, borderTop: 0, borderBottom: 0, borderLeft: 0, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '32px 24px' }}>
                <h2 style={{ fontSize: '1.25rem', color: 'var(--primary)', letterSpacing: '0.5px' }}>SellBot Admin</h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>VPN Management Panel</p>
            </div>

            <nav style={{ flex: 1, padding: '0 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `btn ${isActive ? 'btn-primary' : 'btn-ghost'}`}
                        style={{ justifyContent: 'flex-start', padding: '12px 16px', width: '100%' }}
                    >
                        {item.icon}
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            <div style={{ padding: '24px 16px' }}>
                <button className="btn btn-danger" onClick={onLogout} style={{ width: '100%', justifyContent: 'center' }}>
                    <LogOut size={18} />
                    Logout
                </button>
            </div>
        </aside>
    )
}
