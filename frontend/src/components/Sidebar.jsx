import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Server, Users, LogOut, Send } from 'lucide-react';

export default function Sidebar({ onLogout }) {
    const navItems = [
        { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
        { name: 'Active Plans', path: '/plans', icon: <Server size={20} /> },
        { name: 'User Orders', path: '/orders', icon: <Users size={20} /> },
        { name: 'Broadcast', path: '/broadcast', icon: <Send size={20} /> },
    ];

    return (
        <aside className="sidebar flex-col" style={{ width: '280px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '36px 32px' }}>
                <h2 style={{ fontSize: '1.5rem', color: 'var(--text-main)', letterSpacing: '-0.02em', margin: 0 }}>SellBot<span style={{ color: 'var(--primary)' }}>.</span></h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>VPN Management Panel</p>
            </div>

            <nav style={{ flex: 1, padding: '0 20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    >
                        <span style={{ color: 'inherit' }}>{item.icon}</span>
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            <div style={{ padding: '32px 20px' }}>
                <button className="btn btn-danger" onClick={onLogout} style={{ width: '100%' }}>
                    <LogOut size={18} />
                    Logout
                </button>
            </div>
        </aside>
    )
}
