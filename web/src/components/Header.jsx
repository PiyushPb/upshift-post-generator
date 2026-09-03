import React, { useState, useEffect } from 'react';
import { FirestoreService } from '../services/firestore';

export function Header({ activeTab, setActiveTab }) {
  const [istTime, setIstTime] = useState('');
  const [firestoreStatus, setFirestoreStatus] = useState({ ok: null, latency: null });

  // Update IST clock every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options = {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      };
      setIstTime(new Intl.DateTimeFormat('en-US', options).format(now));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Ping Firestore every 30 seconds
  useEffect(() => {
    const checkStatus = async () => {
      const res = await FirestoreService.ping();
      setFirestoreStatus({ ok: res.ok, latency: res.latencyMs });
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'counter', label: '🔢 Post ID Control', icon: '⚡' },
    { id: 'batches', label: '📦 Published Batches', icon: '📂' },
    { id: 'timetable', label: '📅 Weekly Timetable', icon: '⏰' },
    { id: 'dispatch', label: '🚀 Dispatch Helper', icon: '⚙️' },
  ];

  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(11, 15, 25, 0.85)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3B82F6 0%, #10B981 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.4rem',
            boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)'
          }}>
            ⚡
          </div>
          <div>
            <h1 style={{ fontSize: '1.3rem', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px' }}>
              UPSHIFT <span style={{ color: 'var(--color-primary)', fontWeight: 400 }}>HUB</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.02em' }}>
              AUTOMATED PIPELINE & CLOUD MANAGER
            </p>
          </div>
        </div>

        {/* Live System Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* IST Clock */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem'
          }}>
            <span style={{ color: 'var(--color-primary)' }}>⏰</span>
            <span style={{ color: 'var(--text-secondary)' }}>IST:</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{istTime || 'Loading...'}</span>
          </div>

          {/* Firestore Status */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            padding: '6px 14px',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.82rem'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: firestoreStatus.ok ? '#10B981' : firestoreStatus.ok === false ? '#EF4444' : '#F59E0B',
              boxShadow: firestoreStatus.ok ? '0 0 10px #10B981' : 'none'
            }} />
            <span style={{ color: 'var(--text-secondary)' }}>Firestore:</span>
            <span style={{ fontWeight: 600, color: firestoreStatus.ok ? '#10B981' : '#EF4444' }}>
              {firestoreStatus.ok ? `Online (${firestoreStatus.latency}ms)` : firestoreStatus.ok === false ? 'Offline' : 'Connecting...'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Bar */}
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '0 24px',
        display: 'flex',
        gap: '8px',
        overflowX: 'auto'
      }}>
        {navItems.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
                color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                padding: '12px 16px',
                fontFamily: 'var(--font-heading)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.95rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap'
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
