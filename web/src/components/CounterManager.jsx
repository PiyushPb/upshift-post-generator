import React, { useState, useEffect } from 'react';
import { FirestoreService } from '../services/firestore';

export function CounterManager({ onNotify }) {
  const [loading, setLoading] = useState(true);
  const [counterData, setCounterData] = useState({
    global_counter: 1,
    categories: { engineering: 1, data: 1, devops: 1, product: 1 },
    last_updated_at: null,
    last_post_id: null
  });

  const [isEditingGlobal, setIsEditingGlobal] = useState(false);
  const [customValue, setCustomValue] = useState('');
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetTarget, setResetTarget] = useState(1);
  const [saving, setSaving] = useState(false);

  // Load counter from Firestore on mount
  const loadCounter = async () => {
    setLoading(true);
    try {
      const data = await FirestoreService.getPostCounter();
      setCounterData(data);
      setCustomValue(data.global_counter.toString());
    } catch (err) {
      onNotify(`Error loading counter: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCounter();
  }, []);

  // Update Global Counter
  const handleUpdateGlobal = async (newValue) => {
    const val = parseInt(newValue, 10);
    if (isNaN(val) || val < 1) {
      onNotify('Post ID must be a positive integer (>= 1)', 'error');
      return;
    }
    setSaving(true);
    try {
      const updated = await FirestoreService.updatePostCounter(val, counterData.categories);
      setCounterData((prev) => ({
        ...prev,
        global_counter: updated.global_counter,
        last_updated_at: updated.last_updated_at,
        last_post_id: updated.last_post_id
      }));
      setIsEditingGlobal(false);
      onNotify(`Post ID updated to UP-${String(val).padStart(4, '0')} in Firestore!`, 'success');
    } catch (err) {
      onNotify(`Failed to update counter: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  // Step Global (+1 / -1)
  const handleStepGlobal = (delta) => {
    const nextVal = Math.max(1, counterData.global_counter + delta);
    handleUpdateGlobal(nextVal);
  };

  // Reset Counter Modal Submit
  const handleExecuteReset = async () => {
    setSaving(true);
    try {
      const target = parseInt(resetTarget, 10) || 1;
      await FirestoreService.resetPostCounter(target);
      await loadCounter();
      setShowResetModal(false);
      onNotify(`Counter successfully reset to UP-${String(target).padStart(4, '0')}!`, 'success');
    } catch (err) {
      onNotify(`Reset failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  // Adjust Category Counter
  const handleStepCategory = async (catKey, delta) => {
    const currentCatCount = counterData.categories[catKey] || 1;
    const newCatCount = Math.max(1, currentCatCount + delta);
    const updatedCategories = {
      ...counterData.categories,
      [catKey]: newCatCount
    };
    setSaving(true);
    try {
      await FirestoreService.updatePostCounter(counterData.global_counter, updatedCategories);
      setCounterData((prev) => ({
        ...prev,
        categories: updatedCategories
      }));
      onNotify(`Updated ${catKey.toUpperCase()} counter to #${newCatCount}`, 'success');
    } catch (err) {
      onNotify(`Failed to update category counter: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const formattedCurrentId = `UP-${String(counterData.global_counter).padStart(4, '0')}`;
  const formattedNextId = `UP-${String(counterData.global_counter + 1).padStart(4, '0')}`;

  const categoryMeta = [
    { key: 'engineering', label: 'Engineering', color: 'var(--cat-engineering)', bg: 'var(--cat-engineering-bg)', border: 'rgba(59, 130, 246, 0.3)', icon: '💻' },
    { key: 'data', label: 'Data & AI', color: 'var(--cat-data)', bg: 'var(--cat-data-bg)', border: 'rgba(236, 72, 153, 0.3)', icon: '📊' },
    { key: 'devops', label: 'DevOps & Cloud', color: 'var(--cat-devops)', bg: 'var(--cat-devops-bg)', border: 'rgba(16, 185, 129, 0.3)', icon: '☁️' },
    { key: 'product', label: 'Product & Design', color: 'var(--cat-product)', bg: 'var(--cat-product-bg)', border: 'rgba(245, 158, 11, 0.3)', icon: '🎨' },
  ];

  if (loading) {
    return (
      <div style={{ padding: '60px 0', textAlign: 'center' }}>
        <div style={{ fontSize: '2rem', marginBottom: '12px' }}>⚡</div>
        <p style={{ color: 'var(--text-secondary)' }}>Connecting to Firestore & loading counter state...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Banner & Quick Explanation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', color: '#FFFFFF' }}>Post ID & Counter Controller</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Directly update, bump, or reset sequential post identifiers stored in Firebase Firestore without touching code.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary btn-sm" onClick={loadCounter} disabled={saving}>
            🔄 Refresh
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => setShowResetModal(true)} disabled={saving}>
            ⚠️ Reset Counter...
          </button>
        </div>
      </div>

      {/* Hero Active Post ID Card */}
      <div className="glass-panel" style={{
        padding: '36px',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.85) 0%, rgba(30, 41, 59, 0.6) 100%)'
      }}>
        {/* Glow accent */}
        <div style={{
          position: 'absolute',
          top: '-40px',
          right: '-40px',
          width: '200px',
          height: '200px',
          borderRadius: '50%',
          background: 'var(--color-primary-glow)',
          filter: 'blur(60px)',
          pointerEvents: 'none'
        }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '24px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span className="badge badge-engineering">CANONICAL ACTIVE ID</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Next post will be rendered with this ID
              </span>
            </div>

            {isEditingGlobal ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '12px' }}>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={customValue}
                  onChange={(e) => setCustomValue(e.target.value)}
                  style={{ width: '180px', fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}
                  autoFocus
                />
                <button
                  className="btn btn-primary"
                  onClick={() => handleUpdateGlobal(customValue)}
                  disabled={saving}
                >
                  Save ID
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setIsEditingGlobal(false);
                    setCustomValue(counterData.global_counter.toString());
                  }}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '16px' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '3.5rem',
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textShadow: '0 0 24px rgba(59, 130, 246, 0.4)',
                  letterSpacing: '0.02em'
                }}>
                  {formattedCurrentId}
                </span>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setIsEditingGlobal(true)}
                  style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  ✏️ Edit
                </button>
              </div>
            )}

            <div style={{ display: 'flex', gap: '20px', marginTop: '16px', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Next in queue: </span>
                <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{formattedNextId}</strong>
              </div>
              {counterData.last_post_id && (
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Last published: </span>
                  <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{counterData.last_post_id}</strong>
                </div>
              )}
              {counterData.last_updated_at && (
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Last updated: </span>
                  <span>{new Date(counterData.last_updated_at).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>

          {/* Quick Adjustment Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Quick Bump / Step
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => handleStepGlobal(-1)}
                disabled={saving || counterData.global_counter <= 1}
                title="Decrement counter by 1"
              >
                -1 Step
              </button>
              <button
                className="btn btn-primary"
                onClick={() => handleStepGlobal(1)}
                disabled={saving}
                title="Increment counter by 1"
              >
                +1 Step
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Category Sub-Counters Grid */}
      <div>
        <div style={{ marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1.2rem', color: '#FFFFFF' }}>Category Sub-Counters</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Track total batches published per category. Incremented automatically by pipeline runs or adjustable manually here.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px'
        }}>
          {categoryMeta.map((cat) => {
            const count = counterData.categories[cat.key] || 1;
            return (
              <div
                key={cat.key}
                className="glass-panel"
                style={{
                  padding: '20px',
                  background: 'var(--bg-surface)',
                  border: `1px solid ${cat.border}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '1.2rem' }}>{cat.icon}</span>
                    <span style={{ fontWeight: 600, color: cat.color }}>{cat.label}</span>
                  </div>
                  <span className="badge" style={{ background: cat.bg, color: cat.color, border: `1px solid ${cat.border}` }}>
                    #{count}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '2rem',
                    fontWeight: 700,
                    color: '#FFFFFF'
                  }}>
                    {count}
                  </span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleStepCategory(cat.key, -1)}
                      disabled={saving || count <= 1}
                    >
                      -
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleStepCategory(cat.key, 1)}
                      disabled={saving}
                      style={{ color: cat.color }}
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Confirmation Reset Modal */}
      {showResetModal && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <h3 style={{ fontSize: '1.3rem', color: '#F87171', marginBottom: '8px' }}>
              ⚠️ Reset Post ID Counter
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
              Resetting will update the canonical counter stored in Firebase Firestore. The next automated or manual pipeline run will pick up from this new ID.
            </p>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Reset Global Starting Number:
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>UP-</span>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={resetTarget}
                  onChange={(e) => setResetTarget(e.target.value)}
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}
                />
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                Default is 1 (UP-0001). Category counts will also reset to 1.
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button className="btn btn-secondary" onClick={() => setShowResetModal(false)} disabled={saving}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleExecuteReset} disabled={saving}>
                {saving ? 'Resetting...' : 'Confirm Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
