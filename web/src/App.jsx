import React, { useState } from 'react';
import { Header } from './components/Header';
import { CounterManager } from './components/CounterManager';
import { BatchesExplorer } from './components/BatchesExplorer';
import { TimetableMatrix } from './components/TimetableMatrix';
import { DispatchHelper } from './components/DispatchHelper';

export default function App() {
  const [activeTab, setActiveTab] = useState('counter');
  const [toast, setToast] = useState(null);

  const showNotification = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '32px 24px 80px',
        width: '100%',
        flex: 1
      }}>
        {activeTab === 'counter' && <CounterManager onNotify={showNotification} />}
        {activeTab === 'batches' && <BatchesExplorer onNotify={showNotification} />}
        {activeTab === 'timetable' && <TimetableMatrix />}
        {activeTab === 'dispatch' && <DispatchHelper onNotify={showNotification} />}
      </main>

      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: toast.type === 'error' ? '#EF4444' : '#10B981',
          color: '#FFFFFF',
          padding: '12px 20px',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.4)',
          fontWeight: 600,
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          zIndex: 2000,
          animation: 'slideUp 0.2s ease'
        }}>
          <span>{toast.type === 'error' ? '⚠️' : '✅'}</span>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '24px',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '0.85rem'
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            ⚡ Upshift Automated Job Pipeline Control Hub • Firebase Project: <code style={{ color: 'var(--color-primary)' }}>upshiftjobs</code>
          </div>
          <div>
            Slot 1: 1:00 PM IST • Slot 2: 6:00 PM IST
          </div>
        </div>
      </footer>
    </div>
  );
}
