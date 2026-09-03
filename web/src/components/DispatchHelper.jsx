import React, { useState } from 'react';

export function DispatchHelper({ onNotify }) {
  const [mode, setMode] = useState('auto');
  const [category, setCategory] = useState('engineering');
  const [slot, setSlot] = useState('1');
  const [day, setDay] = useState('today');
  const [location, setLocation] = useState('Bengaluru');
  const [topN, setTopN] = useState(10);
  const [dryRun, setDryRun] = useState(false);
  const [enforceWindow, setEnforceWindow] = useState(false);

  const buildCliCommand = () => {
    let cmd = 'python main.py';
    if (mode === 'auto') {
      cmd += ' --auto-schedule';
    } else {
      cmd += ` --category ${category}`;
    }

    if (slot && slot !== 'current_time') {
      cmd += ` --slot ${slot}`;
    }

    if (day && day !== 'today') {
      cmd += ` --day ${day}`;
    }

    if (location) {
      cmd += ` --location "${location}"`;
    }

    if (topN && topN !== 10) {
      cmd += ` --top ${topN}`;
    }

    if (dryRun) {
      cmd += ' --no-publish';
    }

    if (enforceWindow) {
      cmd += ' --enforce-window';
    }

    cmd += ' --clear-tmp';
    return cmd;
  };

  const handleCopyCommand = () => {
    const cmd = buildCliCommand();
    navigator.clipboard.writeText(cmd);
    onNotify('Copied command to clipboard!', 'success');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', color: '#FFFFFF' }}>Pipeline Dispatcher & CLI Builder</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Configure arguments with visual dropdowns to generate commands or trigger manual runs without editing code.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '24px'
      }}>
        {/* Controls Form */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ fontSize: '1.2rem', color: '#FFFFFF' }}>Run Configuration</h3>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              Execution Mode
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                className={`btn ${mode === 'auto' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                style={{ flex: 1 }}
                onClick={() => setMode('auto')}
              >
                Auto (Timetable)
              </button>
              <button
                className={`btn ${mode === 'manual' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                style={{ flex: 1 }}
                onClick={() => setMode('manual')}
              >
                Manual Override
              </button>
            </div>
          </div>

          {mode === 'manual' && (
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Job Category
              </label>
              <select className="form-select" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="engineering">Engineering (Blue Theme)</option>
                <option value="data">Data & Analytics (Pink Theme)</option>
                <option value="devops">DevOps & Cloud (Green Theme)</option>
                <option value="product">Product & Design (Yellow Theme)</option>
              </select>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Time Slot
              </label>
              <select className="form-select" value={slot} onChange={(e) => setSlot(e.target.value)}>
                <option value="1">Slot 1 (1:00 PM IST)</option>
                <option value="2">Slot 2 (6:00 PM IST)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Day Override
              </label>
              <select className="form-select" value={day} onChange={(e) => setDay(e.target.value)}>
                <option value="today">Today's Schedule</option>
                <option value="monday">Monday</option>
                <option value="tuesday">Tuesday</option>
                <option value="wednesday">Wednesday</option>
                <option value="thursday">Thursday</option>
                <option value="friday">Friday</option>
                <option value="saturday">Saturday</option>
                <option value="sunday">Sunday</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              Target City (India)
            </label>
            <input
              type="text"
              className="form-input"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Bengaluru, Hyderabad, Pune, Mumbai"
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
              />
              <span>Dry Run (Skip publishing to Telegram)</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={enforceWindow}
                onChange={(e) => setEnforceWindow(e.target.checked)}
              />
              <span>Enforce Strict Time Window (Prevents off-hour dispatch)</span>
            </label>
          </div>
        </div>

        {/* Command Preview Card */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', color: '#FFFFFF', marginBottom: '12px' }}>
              Generated Execution Command
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '16px' }}>
              Copy this command to run locally in terminal or test against Firebase & Telegram.
            </p>

            <div style={{
              background: '#0B0F19',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.9rem',
              color: '#34D399',
              wordBreak: 'break-all',
              lineHeight: 1.6
            }}>
              {buildCliCommand()}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button className="btn btn-primary" onClick={handleCopyCommand}>
              📋 Copy Terminal Command
            </button>

            <div style={{
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '12px',
              fontSize: '0.82rem',
              color: 'var(--text-secondary)'
            }}>
              💡 <strong>GitHub Actions Tip:</strong> In your GitHub repo under <em>Actions &rarr; Daily Upshift Job Post Pipeline &rarr; Run workflow</em>, you can run this exact schedule with a single click.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
