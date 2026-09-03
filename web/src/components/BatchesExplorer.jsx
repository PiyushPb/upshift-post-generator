import React, { useState, useEffect } from 'react';
import { FirestoreService } from '../services/firestore';

export function BatchesExplorer({ onNotify }) {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Expanded batch state and loaded jobs cache
  const [expandedBatchId, setExpandedBatchId] = useState(null);
  const [batchJobsMap, setBatchJobsMap] = useState({});
  const [loadingJobsBatchId, setLoadingJobsBatchId] = useState(null);

  const loadBatches = async () => {
    setLoading(true);
    try {
      const data = await FirestoreService.getBatches(40);
      setBatches(data);
    } catch (err) {
      onNotify(`Failed to fetch batches: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const handleToggleExpand = async (batch) => {
    const batchId = batch.batch_id || batch.id;
    if (expandedBatchId === batchId) {
      setExpandedBatchId(null);
      return;
    }

    setExpandedBatchId(batchId);

    // If jobs not loaded yet for this batch, fetch them
    if (!batchJobsMap[batchId] && batch.job_ids && batch.job_ids.length) {
      setLoadingJobsBatchId(batchId);
      try {
        const jobs = await FirestoreService.getBatchJobs(batch.job_ids);
        // Sort jobs by rank
        jobs.sort((a, b) => (a.batch_rank || 0) - (b.batch_rank || 0));
        setBatchJobsMap((prev) => ({ ...prev, [batchId]: jobs }));
      } catch (err) {
        onNotify(`Could not load jobs for batch: ${err.message}`, 'error');
      } finally {
        setLoadingJobsBatchId(null);
      }
    }
  };

  const getCategoryClass = (catStr = '') => {
    const lower = String(catStr).toLowerCase();
    if (lower.includes('eng')) return 'badge-engineering';
    if (lower.includes('data')) return 'badge-data';
    if (lower.includes('devops') || lower.includes('cloud') || lower.includes('sre')) return 'badge-devops';
    if (lower.includes('product') || lower.includes('ux')) return 'badge-product';
    return 'badge-engineering';
  };

  const filteredBatches = batches.filter((b) => {
    const matchesSearch =
      (b.post_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (b.category || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (b.location || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (b.batch_id || '').toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCat =
      selectedCategory === 'all' ||
      (b.category || '').toLowerCase().includes(selectedCategory);

    return matchesSearch && matchesCat;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', color: '#FFFFFF' }}>Published Batches & Job Archive</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Inspect curated batches and individual job cards stored in Firebase Firestore.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadBatches} disabled={loading}>
          🔄 Refresh
        </button>
      </div>

      {/* Filters Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ flex: '1', minWidth: '220px' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Search by Post ID (UP-0010), category, or city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div style={{ minWidth: '160px' }}>
          <select
            className="form-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            <option value="eng">Engineering</option>
            <option value="data">Data & AI</option>
            <option value="devops">DevOps</option>
            <option value="product">Product</option>
          </select>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Showing {filteredBatches.length} of {batches.length} batches
        </div>
      </div>

      {/* Batches List */}
      {loading ? (
        <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📂</div>
          Loading published batches from Firestore...
        </div>
      ) : filteredBatches.length === 0 ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No batches found matching your filters.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredBatches.map((batch) => {
            const batchId = batch.batch_id || batch.id;
            const isExpanded = expandedBatchId === batchId;
            const jobs = batchJobsMap[batchId] || [];
            const isLoadingJobs = loadingJobsBatchId === batchId;

            return (
              <div
                key={batchId}
                className="glass-panel"
                style={{
                  padding: '20px',
                  background: isExpanded ? 'rgba(31, 41, 55, 0.7)' : 'var(--bg-surface)'
                }}
              >
                {/* Summary Row */}
                <div
                  onClick={() => handleToggleExpand(batch)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '1.2rem',
                      fontWeight: 700,
                      color: 'var(--color-primary)'
                    }}>
                      {batch.post_id || 'UP-XXXX'}
                    </span>
                    <span className={`badge ${getCategoryClass(batch.category)}`}>
                      {batch.category || 'General'}
                    </span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      📍 {batch.location || 'India'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {batch.created_at ? new Date(batch.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      }) : '—'}
                    </span>
                    <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                      {batch.total_jobs || (batch.job_ids?.length || 0)} JOBS
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {isExpanded ? '▲ Hide' : '▼ View Jobs'}
                    </span>
                  </div>
                </div>

                {/* Expanded Jobs List */}
                {isExpanded && (
                  <div style={{
                    marginTop: '20px',
                    paddingTop: '16px',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                  }}>
                    {isLoadingJobs ? (
                      <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                        Fetching full job details from Firestore...
                      </div>
                    ) : jobs.length === 0 ? (
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        No job documents found for this batch.
                      </div>
                    ) : (
                      jobs.map((job, idx) => (
                        <div
                          key={job.id || idx}
                          style={{
                            background: 'rgba(17, 24, 39, 0.7)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-md)',
                            padding: '12px 16px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '10px'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{
                              fontFamily: 'var(--font-mono)',
                              fontWeight: 700,
                              color: 'var(--text-muted)',
                              width: '24px'
                            }}>
                              #{job.batch_rank || idx + 1}
                            </span>
                            <div>
                              <div style={{ fontWeight: 600, color: '#FFFFFF', fontSize: '0.95rem' }}>
                                {job.title}
                              </div>
                              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                                <strong style={{ color: 'var(--text-primary)' }}>{job.company}</strong> • {job.location || 'India'} • {job.site}
                              </div>
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                            <span style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.85rem',
                              color: '#10B981',
                              fontWeight: 600
                            }}>
                              {job.salary || '₹ Not Disclosed'}
                            </span>

                            {job.job_url && (
                              <a
                                href={job.job_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-secondary btn-sm"
                                style={{ textDecoration: 'none', fontSize: '0.8rem', padding: '4px 10px' }}
                              >
                                Apply ↗
                              </a>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
