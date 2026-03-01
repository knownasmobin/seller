import { useState } from 'react'
import { Send, Users, Zap, CheckCircle, AlertCircle, User } from 'lucide-react'
import { apiFetch } from '../api'

export default function Broadcast() {
    const [message, setMessage] = useState('')
    const [target, setTarget] = useState('all')
    const [sending, setSending] = useState(false)
    const [result, setResult] = useState(null)
    
    // Single user message state
    const [singleUserMode, setSingleUserMode] = useState(false)
    const [telegramID, setTelegramID] = useState('')
    const [singleMessage, setSingleMessage] = useState('')
    const [sendingSingle, setSendingSingle] = useState(false)
    const [singleResult, setSingleResult] = useState(null)

    const handleSend = async () => {
        if (!message.trim()) return

        setSending(true)
        setResult(null)

        try {
            const res = await apiFetch('/admin/broadcast', {
                method: 'POST',
                body: JSON.stringify({ message, target })
            })
            const data = await res.json()

            if (res.ok) {
                const status = data.status || 'success'
                const isSuccess = status === 'success' || status === 'partial_success'
                setResult({
                    success: isSuccess,
                    partial: status === 'partial_success',
                    sent: data.sent ?? 0,
                    failed: data.failed ?? 0,
                    total: data.total ?? 0,
                })
                setMessage('')
            } else {
                setResult({ success: false, error: data.error || 'Unknown error' })
            }
        } catch (err) {
            setResult({ success: false, error: 'Failed to connect to backend' })
        } finally {
            setSending(false)
        }
    }

    const handleSendToUser = async () => {
        if (!singleMessage.trim() || !telegramID.trim()) return

        const telegramIDNum = parseInt(telegramID.trim())
        if (isNaN(telegramIDNum)) {
            setSingleResult({ success: false, error: 'Invalid Telegram ID. Must be a number.' })
            return
        }

        setSendingSingle(true)
        setSingleResult(null)

        try {
            const res = await apiFetch(`/admin/users/${telegramIDNum}/message`, {
                method: 'POST',
                body: JSON.stringify({ message: singleMessage })
            })
            const data = await res.json()

            if (res.ok) {
                setSingleResult({ success: true, telegram_id: data.telegram_id })
                setSingleMessage('')
            } else {
                setSingleResult({ success: false, error: data.error || data.details || 'Unknown error' })
            }
        } catch (err) {
            setSingleResult({ success: false, error: 'Failed to connect to backend' })
        } finally {
            setSendingSingle(false)
        }
    }

    return (
        <div className="page container">
            <div className="mb-8">
                <h1>Broadcast</h1>
                <p style={{ color: 'var(--text-muted)' }}>Send a message to your users via Telegram</p>
            </div>

            {/* Mode Toggle */}
            <div className="mb-6">
                <div className="flex gap-4">
                    <button
                        className={`btn ${!singleUserMode ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setSingleUserMode(false)}
                    >
                        <Users size={18} />
                        Broadcast to Many
                    </button>
                    <button
                        className={`btn ${singleUserMode ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setSingleUserMode(true)}
                    >
                        <User size={18} />
                        Send to Specific User
                    </button>
                </div>
            </div>

            {!singleUserMode ? (
            <div className="flex gap-6" style={{ flexWrap: 'wrap', alignItems: 'flex-start' }}>
                {/* Compose Section */}
                <div className="glass glass-card" style={{ flex: '2 1 400px', animation: 'slideUpFade 0.6s 0.1s both' }}>
                    <h3 style={{ marginBottom: '20px' }}>Compose Message</h3>

                    {/* Target Selector */}
                    <div style={{ marginBottom: '20px' }}>
                        <label className="input-label" style={{ marginBottom: '12px', display: 'block' }}>Audience</label>
                        <div className="flex gap-4">
                            <button
                                className={`btn ${target === 'all' ? 'btn-primary' : 'btn-ghost'}`}
                                onClick={() => setTarget('all')}
                                style={{ flex: 1 }}
                            >
                                <Users size={18} />
                                All Users
                            </button>
                            <button
                                className={`btn ${target === 'active' ? 'btn-primary' : 'btn-ghost'}`}
                                onClick={() => setTarget('active')}
                                style={{ flex: 1 }}
                            >
                                <Zap size={18} />
                                Active Subscribers
                            </button>
                        </div>
                    </div>

                    {/* Message Input */}
                    <div className="input-group">
                        <label className="input-label">Message (Markdown supported)</label>
                        <textarea
                            className="input-field"
                            rows={8}
                            placeholder="Type your message here...&#10;&#10;You can use *bold*, _italic_, and `code` formatting."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            style={{ resize: 'vertical', minHeight: '160px', lineHeight: '1.6' }}
                        />
                    </div>

                    <button
                        className="btn btn-primary"
                        onClick={handleSend}
                        disabled={sending || !message.trim()}
                        style={{ width: '100%', padding: '14px', opacity: (sending || !message.trim()) ? 0.5 : 1 }}
                    >
                        {sending ? (
                            <>
                                <div style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div>
                                Sending...
                            </>
                        ) : (
                            <>
                                <Send size={18} />
                                Send Broadcast
                            </>
                        )}
                    </button>
                </div>

                {/* Preview & Results Section */}
                <div style={{ flex: '1 1 280px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Preview */}
                    <div className="glass glass-card" style={{ animation: 'slideUpFade 0.6s 0.2s both' }}>
                        <h3 style={{ marginBottom: '16px' }}>Preview</h3>
                        <div style={{
                            background: 'rgba(0,0,0,0.3)',
                            borderRadius: '12px',
                            padding: '20px',
                            minHeight: '120px',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            color: 'var(--text-main)',
                            fontSize: '0.95rem',
                            lineHeight: '1.7',
                            fontFamily: 'Inter, sans-serif'
                        }}>
                            {message || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Your message preview will appear here...</span>}
                        </div>
                    </div>

                    {/* Result */}
                    {result && (
                        <div className="glass glass-card" style={{ animation: 'slideUpFade 0.4s ease both', borderColor: result.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)' }}>
                            {result.success ? (
                                <>
                                    <div className="flex items-center gap-4" style={{ marginBottom: '16px' }}>
                                        <CheckCircle size={24} style={{ color: 'var(--success)' }} />
                                        <h3 style={{ margin: 0, color: 'var(--success)' }}>
                                            {result.partial ? 'Sent with Partial Failures' : 'Sent Successfully!'}
                                        </h3>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', textAlign: 'center' }}>
                                        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '12px' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{result.total}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total</div>
                                        </div>
                                        <div style={{ background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', padding: '12px' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)' }}>{result.sent}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sent</div>
                                        </div>
                                        <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', padding: '12px' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--danger)' }}>{result.failed}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Failed</div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex items-center gap-4">
                                    <AlertCircle size={24} style={{ color: 'var(--danger)' }} />
                                    <div>
                                        <h3 style={{ margin: 0, color: 'var(--danger)' }}>Failed</h3>
                                        <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.9rem' }}>{result.error}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Tips */}
                    <div className="glass glass-card" style={{ animation: 'slideUpFade 0.6s 0.3s both' }}>
                        <h3 style={{ marginBottom: '12px', fontSize: '1rem' }}>💡 Tips</h3>
                        <ul style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.8', paddingLeft: '16px' }}>
                            <li>Use <code style={{ background: 'rgba(99,102,241,0.15)', padding: '2px 6px', borderRadius: '4px', color: 'var(--primary)' }}>*bold*</code> for emphasis</li>
                            <li>Use <code style={{ background: 'rgba(99,102,241,0.15)', padding: '2px 6px', borderRadius: '4px', color: 'var(--primary)' }}>_italic_</code> for subtlety</li>
                            <li>"Active Subscribers" targets users with non-expired VPN configs</li>
                        </ul>
                    </div>
                </div>
            </div>
            ) : (
            <div className="flex gap-6" style={{ flexWrap: 'wrap', alignItems: 'flex-start' }}>
                {/* Single User Message Section */}
                <div className="glass glass-card" style={{ flex: '2 1 400px', animation: 'slideUpFade 0.6s 0.1s both' }}>
                    <h3 style={{ marginBottom: '20px' }}>Send Message to User</h3>

                    {/* Telegram ID Input */}
                    <div className="input-group" style={{ marginBottom: '20px' }}>
                        <label htmlFor="telegram-id-input" className="input-label">Telegram User ID</label>
                        <input
                            id="telegram-id-input"
                            type="text"
                            className="input-field"
                            placeholder="123456789"
                            value={telegramID}
                            onChange={(e) => setTelegramID(e.target.value)}
                        />
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>
                            Enter the Telegram ID of the user you want to message
                        </p>
                    </div>

                    {/* Message Input */}
                    <div className="input-group">
                        <label htmlFor="single-message-input" className="input-label">Message (Markdown supported)</label>
                        <textarea
                            id="single-message-input"
                            className="input-field"
                            rows={8}
                            placeholder="Type your message here...&#10;&#10;You can use *bold*, _italic_, and `code` formatting."
                            value={singleMessage}
                            onChange={(e) => setSingleMessage(e.target.value)}
                            style={{ resize: 'vertical', minHeight: '160px', lineHeight: '1.6' }}
                        />
                    </div>

                    <button
                        className="btn btn-primary"
                        onClick={handleSendToUser}
                        disabled={sendingSingle || !singleMessage.trim() || !telegramID.trim()}
                        style={{ width: '100%', padding: '14px', marginTop: '16px', opacity: (sendingSingle || !singleMessage.trim() || !telegramID.trim()) ? 0.5 : 1 }}
                    >
                        {sendingSingle ? (
                            <>
                                <div style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div>
                                Sending...
                            </>
                        ) : (
                            <>
                                <Send size={18} />
                                Send Message
                            </>
                        )}
                    </button>
                </div>

                {/* Preview & Results Section */}
                <div style={{ flex: '1 1 280px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Preview */}
                    <div className="glass glass-card" style={{ animation: 'slideUpFade 0.6s 0.2s both' }}>
                        <h3 style={{ marginBottom: '16px' }}>Preview</h3>
                        <div style={{
                            background: 'rgba(0,0,0,0.3)',
                            borderRadius: '12px',
                            padding: '20px',
                            minHeight: '120px',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            color: 'var(--text-main)',
                            fontSize: '0.95rem',
                            lineHeight: '1.7',
                            fontFamily: 'Inter, sans-serif'
                        }}>
                            {singleMessage || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Your message preview will appear here...</span>}
                        </div>
                    </div>

                    {/* Result */}
                    {singleResult && (
                        <div className="glass glass-card" style={{ animation: 'slideUpFade 0.4s ease both', borderColor: singleResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)' }}>
                            {singleResult.success ? (
                                <div className="flex items-center gap-4">
                                    <CheckCircle size={24} style={{ color: 'var(--success)' }} />
                                    <div>
                                        <h3 style={{ margin: 0, color: 'var(--success)' }}>Message Sent!</h3>
                                        <p style={{ color: 'var(--text-muted)', margin: '8px 0 0 0', fontSize: '0.9rem' }}>
                                            Message sent to user ID: {singleResult.telegram_id}
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center gap-4">
                                    <AlertCircle size={24} style={{ color: 'var(--danger)' }} />
                                    <div>
                                        <h3 style={{ margin: 0, color: 'var(--danger)' }}>Failed</h3>
                                        <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.9rem' }}>{singleResult.error}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Tips */}
                    <div className="glass glass-card" style={{ animation: 'slideUpFade 0.6s 0.3s both' }}>
                        <h3 style={{ marginBottom: '12px', fontSize: '1rem' }}>💡 Tips</h3>
                        <ul style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.8', paddingLeft: '16px' }}>
                            <li>Telegram ID can be found in user orders or subscriptions</li>
                            <li>User must have started a conversation with the bot</li>
                            <li>Use <code style={{ background: 'rgba(99,102,241,0.15)', padding: '2px 6px', borderRadius: '4px', color: 'var(--primary)' }}>*bold*</code> for emphasis</li>
                            <li>Use <code style={{ background: 'rgba(99,102,241,0.15)', padding: '2px 6px', borderRadius: '4px', color: 'var(--primary)' }}>_italic_</code> for subtlety</li>
                        </ul>
                    </div>
                </div>
            </div>
            )}
        </div>
    )
}
