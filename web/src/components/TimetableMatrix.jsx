import React, { useState, useEffect } from 'react';

const WEEKLY_SCHEDULE = {
  monday: {
    slot_1: { category: 'engineering', label: 'Full Stack & Backend', location: 'Bengaluru', search_terms: ['Full Stack Developer', 'Backend Developer', 'Java Developer'] },
    slot_2: { category: 'data', label: 'Data Analytics & BI', location: 'Bengaluru', search_terms: ['Data Analyst', 'Business Analyst', 'Power BI Developer'] }
  },
  tuesday: {
    slot_1: { category: 'devops', label: 'DevOps & Cloud Infrastructure', location: 'Hyderabad', search_terms: ['DevOps Engineer', 'Cloud Engineer', 'AWS Engineer'] },
    slot_2: { category: 'engineering', label: 'Frontend & Mobile Apps', location: 'Bengaluru', search_terms: ['Frontend Developer', 'React Developer', 'Flutter Developer'] }
  },
  wednesday: {
    slot_1: { category: 'data', label: 'AI & Machine Learning', location: 'Bengaluru', search_terms: ['Machine Learning Engineer', 'Data Scientist', 'AI Engineer'] },
    slot_2: { category: 'product', label: 'Product Management & UX', location: 'Mumbai', search_terms: ['Product Manager', 'UI/UX Designer', 'Product Designer'] }
  },
  thursday: {
    slot_1: { category: 'engineering', label: 'Backend & Distributed Systems', location: 'Pune', search_terms: ['Backend Engineer', 'Python Developer', 'Golang Developer'] },
    slot_2: { category: 'devops', label: 'SRE & Platform Engineering', location: 'Bengaluru', search_terms: ['Site Reliability Engineer', 'Platform Engineer', 'Kubernetes Engineer'] }
  },
  friday: {
    slot_1: { category: 'data', label: 'Data Engineering & Pipelines', location: 'Hyderabad', search_terms: ['Data Engineer', 'SQL Developer', 'ETL Developer'] },
    slot_2: { category: 'engineering', label: 'Software & Web Dev', location: 'Gurugram', search_terms: ['Software Engineer', 'React Developer', 'Node.js Developer'] }
  },
  saturday: {
    slot_1: { category: 'engineering', label: 'Weekend Engineering Focus', location: 'Bengaluru', search_terms: ['Software Engineer', 'Full Stack Developer'] },
    slot_2: { category: 'data', label: 'Weekend Data & AI Focus', location: 'Bengaluru', search_terms: ['Data Analyst', 'Data Scientist'] }
  },
  sunday: {
    slot_1: { category: 'product', label: 'Product & Growth', location: 'Bengaluru', search_terms: ['Product Manager', 'Product Analyst', 'UI/UX Designer'] },
    slot_2: { category: 'devops', label: 'Cloud & Cybersecurity', location: 'Bengaluru', search_terms: ['Cloud Architect', 'Security Engineer', 'DevOps Engineer'] }
  }
};

export function TimetableMatrix() {
  const [currentDay, setCurrentDay] = useState('monday');
  const [countdown, setCountdown] = useState('');
  const [nextSlotInfo, setNextSlotInfo] = useState({ slot: 'slot_1', time: '1:00 PM', day: 'today' });

  useEffect(() => {
    const calculateCountdown = () => {
      // Get current IST time
      const now = new Date();
      const istString = now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' });
      const istDate = new Date(istString);

      const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
      const dayName = dayNames[istDate.getDay()];
      setCurrentDay(dayName);

      const hours = istDate.getHours();
      const minutes = istDate.getMinutes();
      const seconds = istDate.getSeconds();
      const currentMinute = hours * 60 + minutes;

      const slot1Minute = 13 * 60; // 1:00 PM (13:00)
      const slot2Minute = 18 * 60; // 6:00 PM (18:00)

      let targetDate = new Date(istDate);
      let nextSlot = 'slot_1';
      let nextTime = '1:00 PM IST';
      let nextDayLabel = 'Today';

      if (currentMinute < slot1Minute) {
        targetDate.setHours(13, 0, 0, 0);
        nextSlot = 'slot_1';
        nextTime = '1:00 PM IST';
      } else if (currentMinute < slot2Minute) {
        targetDate.setHours(18, 0, 0, 0);
        nextSlot = 'slot_2';
        nextTime = '6:00 PM IST';
      } else {
        targetDate.setDate(targetDate.getDate() + 1);
        targetDate.setHours(13, 0, 0, 0);
        nextSlot = 'slot_1';
        nextTime = '1:00 PM IST';
        nextDayLabel = 'Tomorrow';
      }

      setNextSlotInfo({ slot: nextSlot, time: nextTime, day: nextDayLabel });

      const diffMs = targetDate.getTime() - istDate.getTime();
      if (diffMs <= 0) {
        setCountdown('Starting right now!');
      } else {
        const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        const diffSecs = Math.floor((diffMs % (1000 * 60)) / 1000);
        setCountdown(`${diffHrs}h ${diffMins}m ${diffSecs}s`);
      }
    };

    calculateCountdown();
    const interval = setInterval(calculateCountdown, 1000);
    return () => clearInterval(interval);
  }, []);

  const getCategoryBadgeClass = (category) => {
    switch (category) {
      case 'engineering': return 'badge-engineering';
      case 'data': return 'badge-data';
      case 'devops': return 'badge-devops';
      case 'product': return 'badge-product';
      default: return 'badge-engineering';
    }
  };

  const daysList = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header & Next Run Spotlight */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', color: '#FFFFFF' }}>Automated 7-Day Timetable</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Two strict daily slots: <strong>Slot 1 at 1:00 PM IST</strong> and <strong>Slot 2 at 6:00 PM IST</strong>.
          </p>
        </div>

        {/* Countdown Banner */}
        <div className="glass-panel" style={{
          padding: '14px 20px',
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '16px'
        }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              NEXT EXECUTION ({nextSlotInfo.day})
            </div>
            <div style={{ fontWeight: 700, color: '#FFFFFF', fontSize: '1rem' }}>
              {nextSlotInfo.time} ({nextSlotInfo.slot === 'slot_1' ? 'Slot 1' : 'Slot 2'})
            </div>
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '1.4rem',
            fontWeight: 700,
            color: 'var(--color-primary)',
            background: 'rgba(0, 0, 0, 0.3)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)'
          }}>
            {countdown}
          </div>
        </div>
      </div>

      {/* Grid of Days */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '18px'
      }}>
        {daysList.map((day) => {
          const isToday = day === currentDay;
          const schedule = WEEKLY_SCHEDULE[day];

          return (
            <div
              key={day}
              className="glass-panel"
              style={{
                padding: '20px',
                background: isToday ? 'rgba(31, 41, 55, 0.9)' : 'var(--bg-surface)',
                border: isToday ? '2px solid var(--color-primary)' : '1px solid var(--border-subtle)',
                position: 'relative'
              }}
            >
              {isToday && (
                <div style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px'
                }}>
                  <span className="badge badge-engineering" style={{ boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)' }}>
                    TODAY
                  </span>
                </div>
              )}

              <h3 style={{
                textTransform: 'capitalize',
                fontSize: '1.25rem',
                color: isToday ? 'var(--color-primary)' : '#FFFFFF',
                marginBottom: '16px'
              }}>
                {day}
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Slot 1 */}
                <div style={{
                  background: 'rgba(17, 24, 39, 0.75)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                      SLOT 1 (1:00 PM IST)
                    </span>
                    <span className={`badge ${getCategoryBadgeClass(schedule.slot_1.category)}`}>
                      {schedule.slot_1.category}
                    </span>
                  </div>
                  <div style={{ fontWeight: 600, color: '#FFFFFF', fontSize: '0.92rem' }}>
                    {schedule.slot_1.label}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    📍 {schedule.slot_1.location} • Keywords: {schedule.slot_1.search_terms.slice(0, 2).join(', ')}
                  </div>
                </div>

                {/* Slot 2 */}
                <div style={{
                  background: 'rgba(17, 24, 39, 0.75)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                      SLOT 2 (6:00 PM IST)
                    </span>
                    <span className={`badge ${getCategoryBadgeClass(schedule.slot_2.category)}`}>
                      {schedule.slot_2.category}
                    </span>
                  </div>
                  <div style={{ fontWeight: 600, color: '#FFFFFF', fontSize: '0.92rem' }}>
                    {schedule.slot_2.label}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    📍 {schedule.slot_2.location} • Keywords: {schedule.slot_2.search_terms.slice(0, 2).join(', ')}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
