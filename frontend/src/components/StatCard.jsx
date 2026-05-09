import React from 'react';
import { useCountdown } from '../hooks/useCountdown';

/* ─── helpers ──────────────────────────────────────────────────────────── */

const normalizeSignal = (s = '') => {
    const lower = String(s).toLowerCase();
    if (lower === 'green')  return 'green';
    if (lower === 'yellow') return 'yellow';
    if (lower === 'red')    return 'red';
    return 'red';
};

const SIGNAL_CONFIG = {
    green: {
        label: '🟢 GREEN',
        bg: 'rgba(0,255,136,0.1)',
        border: '#00ff88',
        color: '#00ff88',
    },
    yellow: {
        label: '🟡 YELLOW',
        bg: 'rgba(255,215,0,0.1)',
        border: '#ffd700',
        color: '#ffd700',
    },
    red: {
        label: '🔴 RED',
        bg: 'rgba(255,71,87,0.1)',
        border: '#ff4757',
        color: '#ff4757',
    },
};

const PILL_INACTIVE = {
    bg: '#111827',
    border: '#1e293b',
    color: '#4b5563',
};

const CONGESTION_COLOR = {
    low:       '#00ff88',
    medium:    '#ffd700',
    high:      '#ff4757',
    emergency: '#ff6b35',
};

/* ─── component ────────────────────────────────────────────────────────── */

const StatCard = ({
    laneName,
    vehicleCount = 0,
    congestionLevel = 'Low',
    emergency = false,
    signal: rawSignal = 'red',
    duration = 0,
    types = {},
    breakdown = {},
}) => {
    const signal = emergency ? 'emergency' : normalizeSignal(rawSignal);
    const activeSignal = emergency ? 'green' : normalizeSignal(rawSignal);

    /* Live countdown */
    const countdown = useCountdown(duration, activeSignal);
    const isUrgent   = countdown > 0 && countdown <= 5;
    const isCritical = countdown > 0 && countdown <= 3;

    /* Header badge */
    const headerBadge = emergency
        ? { label: '🚨 EMERGENCY', bg: 'rgba(255,107,53,0.15)', border: '#ff6b35', color: '#ff6b35' }
        : SIGNAL_CONFIG[activeSignal];

    /* Congestion colour */
    const congKey = (emergency ? 'emergency' : congestionLevel).toLowerCase();
    const congColor = CONGESTION_COLOR[congKey] || '#e2e8f0';

    /* Vehicle types — prefer backend `types`, fall back to `breakdown` */
    const typesSource = Object.keys(types).length > 0 ? types : breakdown;
    const typeEntries = Object.entries(typesSource).filter(([, v]) => v > 0);

    /* Signal time text colour (with urgency override) */
    const baseSignalColor = activeSignal === 'green' ? '#00ff88' : activeSignal === 'yellow' ? '#ffd700' : '#ff4757';
    const durationColor = countdown === 0
        ? '#475569'
        : isCritical ? '#ff4757'
        : isUrgent   ? '#ff6b35'
        : baseSignalColor;

    /* Panel border / glow */
    const panelStyle = {
        background:   '#0f1623',
        border:       emergency ? '1px solid rgba(255,107,53,0.4)' : '1px solid #1a2535',
        borderRadius: '14px',
        padding:      '20px',
        marginTop:    '16px',
        transition:   'border 0.3s ease, box-shadow 0.3s ease',
        boxShadow:    emergency ? '0 0 20px rgba(255,107,53,0.1)' : 'none',
    };

    /* Signal pills — active pill shows live countdown with urgency colours */
    const signalPills = ['green', 'yellow', 'red'].map(s => {
        const isActive = s === activeSignal;
        const cfg = SIGNAL_CONFIG[s];
        const pillColor = isActive
            ? (isCritical ? '#ff4757' : isUrgent ? '#ff6b35' : cfg.color)
            : PILL_INACTIVE.color;
        const pillBorder = isActive
            ? (isCritical ? '#ff4757' : isUrgent ? '#ff6b35' : cfg.border)
            : PILL_INACTIVE.border;
        const pillBg = isActive
            ? (isCritical ? 'rgba(255,71,87,0.15)' : isUrgent ? 'rgba(255,107,53,0.12)' : cfg.bg)
            : PILL_INACTIVE.bg;
        return {
            key:    s,
            label:  s === 'green' ? '🟢' : s === 'yellow' ? '🟡' : '🔴',
            name:   s.charAt(0).toUpperCase() + s.slice(1),
            value:  isActive ? countdown : 0,
            active: isActive,
            bg:     pillBg,
            border: pillBorder,
            color:  pillColor,
            blink:  isActive && isCritical,
        };
    });

    return (
        <div style={panelStyle}>

            {/* ── Header ─────────────────────────────────────────────── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{
                    fontFamily:  "'Rajdhani', 'Orbitron', sans-serif",
                    fontSize:    '18px',
                    fontWeight:  700,
                    color:       '#f1f5f9',
                    display:     'flex',
                    alignItems:  'center',
                    gap:         '6px',
                }}>
                    📍 {laneName}
                </span>
                <span style={{
                    background:   headerBadge.bg,
                    border:       `1px solid ${headerBadge.border}`,
                    color:        headerBadge.color,
                    borderRadius: '20px',
                    padding:      '4px 14px',
                    fontSize:     '13px',
                    fontWeight:   600,
                    transition:   'all 0.3s ease',
                    whiteSpace:   'nowrap',
                }}>
                    {headerBadge.label}
                </span>
            </div>

            {/* ── Divider ─────────────────────────────────────────────── */}
            <div style={{ borderTop: '1px solid #1a2535', margin: '12px 0' }} />

            {/* ── Emergency banner ────────────────────────────────────── */}
            {emergency && (
                <div style={{
                    background:   'rgba(255,107,53,0.1)',
                    border:       '1px solid rgba(255,107,53,0.3)',
                    borderRadius: '8px',
                    padding:      '8px 14px',
                    marginBottom: '14px',
                    color:        '#ff6b35',
                    fontSize:     '13px',
                    textAlign:    'center',
                    animation:    'fadeIn 0.3s ease',
                }}>
                    🚨 Emergency Vehicle In Lane — Priority GREEN Signal
                </div>
            )}

            {/* ── Big vehicle count ───────────────────────────────────── */}
            <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                <div style={{
                    fontFamily:  "'Rajdhani', 'Orbitron', sans-serif",
                    fontSize:    '56px',
                    fontWeight:  700,
                    color:       '#ffffff',
                    lineHeight:  1,
                    transition:  'all 0.3s ease',
                }}>
                    {vehicleCount}
                </div>
                <div style={{
                    fontSize:      '11px',
                    color:         '#475569',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    marginTop:     '4px',
                }}>
                    vehicles in lane
                </div>
            </div>

            {/* ── Signal pills row ────────────────────────────────────── */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                {signalPills.map(pill => (
                    <span
                        key={pill.key}
                        style={{
                            background:   pill.bg,
                            border:       `1px solid ${pill.border}`,
                            color:        pill.color,
                            borderRadius: '20px',
                            padding:      '5px 14px',
                            fontSize:     '13px',
                            fontWeight:   600,
                            transition:   'all 0.3s ease',
                            whiteSpace:   'nowrap',
                            animation:    pill.blink ? 'countdown-blink 0.5s step-start infinite' : 'none',
                        }}
                    >
                        {pill.label} {pill.name}: {pill.value}s
                    </span>
                ))}
            </div>

            {/* ── Divider ─────────────────────────────────────────────── */}
            <div style={{ borderTop: '1px solid #1a2535', margin: '0 0 4px 0' }} />

            {/* ── Info rows ───────────────────────────────────────────── */}

            {/* Row: Congestion */}
            <div style={rowStyle}>
                <span style={keyStyle}>CONGESTION</span>
                <span style={{ ...valStyle, color: congColor, fontWeight: congKey === 'emergency' ? 700 : 500 }}>
                    {congestionLevel}
                </span>
            </div>

            {/* Row: Emergency */}
            <div style={rowStyle}>
                <span style={keyStyle}>EMERGENCY</span>
                {emergency
                    ? <span style={{ color: '#ff6b35', fontWeight: 700, fontSize: '13px' }}>YES 🚨</span>
                    : <span style={{ color: '#334155', fontWeight: 500, fontSize: '13px' }}>NO</span>
                }
            </div>

            {/* Row: Vehicle types */}
            <div style={rowStyle}>
                <span style={keyStyle}>VEHICLE TYPES</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'flex-end', gap: '4px' }}>
                    {typeEntries.length > 0
                        ? typeEntries.map(([type, count]) => (
                            <span key={type} style={badgeStyle}>
                                {type}: {count}
                            </span>
                        ))
                        : <span style={{ color: '#334155', fontSize: '13px' }}>—</span>
                    }
                </div>
            </div>

            {/* Row: Signal time — no bottom border */}
            <div style={{ ...rowStyle, borderBottom: 'none' }}>
                <span style={keyStyle}>SIGNAL TIME</span>
                <span style={{
                    color:      durationColor,
                    fontWeight: 600,
                    fontSize:   '13px',
                    transition: 'color 0.3s ease',
                    animation:  isCritical ? 'countdown-blink 0.5s step-start infinite' : 'none',
                }}>
                    {countdown} seconds remaining
                </span>
            </div>
        </div>
    );
};

/* ─── shared row / badge styles ────────────────────────────────────────── */

const rowStyle = {
    display:       'flex',
    justifyContent:'space-between',
    alignItems:    'center',
    padding:       '8px 0',
    borderBottom:  '1px solid #0f172a',
    flexWrap:      'wrap',
    gap:           '4px',
};

const keyStyle = {
    color:         '#475569',
    fontSize:      '11px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    fontWeight:    500,
    flexShrink:    0,
};

const valStyle = {
    color:      '#e2e8f0',
    fontWeight: 500,
    fontSize:   '13px',
};

const badgeStyle = {
    background:   '#111827',
    border:       '1px solid #1a2535',
    borderRadius: '4px',
    padding:      '2px 8px',
    fontSize:     '12px',
    color:        '#94a3b8',
};

/* ─── keyframe injection (once) ────────────────────────────────────────── */

if (typeof document !== 'undefined' && !document.getElementById('statcard-keyframes')) {
    const style = document.createElement('style');
    style.id = 'statcard-keyframes';
    style.textContent = `
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&display=swap');
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes countdown-blink { 50% { opacity: 0; } }
    `;
    document.head.appendChild(style);
}

export default StatCard;
