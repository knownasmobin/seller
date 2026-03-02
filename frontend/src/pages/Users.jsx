import { useState, useEffect } from 'react'
import { Users as UsersIcon, UserPlus, Search, UserCheck } from 'lucide-react'
import { apiFetch } from '../api'

export default function Users() {
    const [users, setUsers] = useState([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [filterInvitedBy, setFilterInvitedBy] = useState('')

    useEffect(() => {
        fetchUsers()
    }, [])

    const fetchUsers = async () => {
        try {
            const res = await apiFetch('/admin/users')
            if (res.ok) {
                const data = await res.json()
                setUsers(data || [])
            }
        } catch (err) {
            console.error("Failed to fetch users", err)
        } finally {
            setLoading(false)
        }
    }

    const filteredUsers = users.filter(user => {
        const matchesSearch = searchTerm === '' || 
            user.telegram_id.toString().includes(searchTerm) ||
            (user.username && user.username.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (user.invited_by && user.invited_by.toString().includes(searchTerm))
        const matchesFilter = filterInvitedBy === '' || 
            (filterInvitedBy === 'none' && user.invited_by === 0) ||
            (filterInvitedBy !== 'none' && user.invited_by.toString() === filterInvitedBy)
        return matchesSearch && matchesFilter
    })

    const getInviterName = (invitedBy) => {
        if (invitedBy === 0) return '—'
        const inviter = users.find(u => u.telegram_id === invitedBy)
        if (inviter) {
            return inviter.username ? `@${inviter.username}` : `@${inviter.telegram_id}`
        }
        return `@${invitedBy}`
    }

    const totalReferrals = users.reduce((sum, u) => sum + (u.referral_count || 0), 0)
    const usersWithReferrals = users.filter(u => (u.referral_count || 0) > 0).length

    if (loading) {
        return (
            <div className="page container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ width: 40, height: 40, border: '3px solid var(--glass-border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }}></div>
                    Loading users...
                </div>
            </div>
        )
    }

    return (
        <div className="page container">
            <div className="mb-8">
                <h1>Users</h1>
                <p style={{ color: 'var(--text-muted)' }}>Manage and track user referrals and invite relationships</p>
            </div>

            {/* Stats Cards */}
            <div className="flex gap-6 mb-8" style={{ flexWrap: 'wrap' }}>
                <div className="glass glass-card" style={{ flex: '1 1 200px', animation: 'slideUpFade 0.6s 0.1s both' }}>
                    <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Users</h3>
                        <span style={{ color: 'var(--primary)', padding: '8px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px' }}><UsersIcon size={20} /></span>
                    </div>
                    <span style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                        {users.length.toLocaleString()}
                    </span>
                </div>
                <div className="glass glass-card" style={{ flex: '1 1 200px', animation: 'slideUpFade 0.6s 0.2s both' }}>
                    <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Referrals</h3>
                        <span style={{ color: 'var(--success)', padding: '8px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px' }}><UserPlus size={20} /></span>
                    </div>
                    <span style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                        {totalReferrals.toLocaleString()}
                    </span>
                </div>
                <div className="glass glass-card" style={{ flex: '1 1 200px', animation: 'slideUpFade 0.6s 0.3s both' }}>
                    <div className="flex justify-between items-center" style={{ marginBottom: '16px' }}>
                        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Active Referrers</h3>
                        <span style={{ color: '#8b5cf6', padding: '8px', background: 'rgba(139, 92, 246, 0.1)', borderRadius: '8px' }}><UserCheck size={20} /></span>
                    </div>
                    <span style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                        {usersWithReferrals.toLocaleString()}
                    </span>
                </div>
            </div>

            {/* Filters */}
            <div className="glass glass-card mb-8" style={{ animation: 'slideUpFade 0.6s 0.4s both' }}>
                <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
                    <div style={{ position: 'relative', flex: '1 1 300px' }}>
                        <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            type="text"
                            className="input-field"
                            placeholder="Search by Telegram ID, Username, or Inviter ID..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            style={{ paddingLeft: '44px', marginBottom: 0 }}
                        />
                    </div>
                    <div style={{ flex: '1 1 200px' }}>
                        <select
                            className="input-field"
                            value={filterInvitedBy}
                            onChange={(e) => setFilterInvitedBy(e.target.value)}
                            style={{ marginBottom: 0 }}
                        >
                            <option value="">All Users</option>
                            <option value="none">No Inviter (Direct/Admin)</option>
                            {Array.from(new Set(users.filter(u => u.invited_by > 0).map(u => u.invited_by))).map(id => (
                                <option key={id} value={id.toString()}>Invited by @{id}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Users Table */}
            <div className="glass" style={{ overflow: 'hidden', animation: 'slideUpFade 0.6s 0.5s both' }}>
                <div style={{ padding: '24px 28px 16px' }}>
                    <h2 style={{ fontSize: '1.5rem', margin: 0 }}>All Users ({filteredUsers.length})</h2>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Telegram ID</th>
                            <th>Username</th>
                            <th>Invited By</th>
                            <th>Referrals</th>
                            <th>Balance</th>
                            <th>Language</th>
                            <th>Admin</th>
                            <th>Joined</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredUsers.length === 0 ? (
                            <tr>
                                <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                                    {searchTerm || filterInvitedBy ? 'No users match your filters.' : 'No users yet.'}
                                </td>
                            </tr>
                        ) : (
                            filteredUsers.map(user => (
                                <tr key={user.id}>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.9rem', fontWeight: 600 }}>
                                        @{user.telegram_id}
                                    </td>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.9rem', color: user.username ? 'var(--text-main)' : 'var(--text-muted)' }}>
                                        {user.username ? `@${user.username}` : '—'}
                                    </td>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.9rem', color: user.invited_by === 0 ? 'var(--text-muted)' : 'var(--text-main)' }}>
                                        {getInviterName(user.invited_by)}
                                    </td>
                                    <td>
                                        <span style={{ 
                                            color: (user.referral_count || 0) > 0 ? 'var(--success)' : 'var(--text-muted)',
                                            fontWeight: (user.referral_count || 0) > 0 ? 600 : 400
                                        }}>
                                            {user.referral_count || 0}
                                        </span>
                                    </td>
                                    <td>{user.balance?.toLocaleString() || '0'}</td>
                                    <td>
                                        <span className="badge badge-primary" style={{ textTransform: 'uppercase' }}>
                                            {user.language || 'fa'}
                                        </span>
                                    </td>
                                    <td>
                                        {user.is_admin ? (
                                            <span className="badge badge-warning">Admin</span>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)' }}>—</span>
                                        )}
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
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

