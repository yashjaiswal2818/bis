import React from 'react';

/**
 * The struck-medallion mark. One drawn asset, reused everywhere a "this is
 * verified / this is the standard" signal is needed: the brand mark, and the
 * confidence ring on every result. The fill ratio of the inner arc *is* the
 * confidence reading -- not a decoration next to it.
 */
const TIER_STYLE = {
  brand:  { ring: '#0C4DA1', arc: '#0C4DA1', glyph: '#FFFFFF', fill: 'solid', sweep: 1 },
  high:   { ring: '#0C4DA1', arc: '#0C4DA1', glyph: '#FFFFFF', fill: 'solid', sweep: 1 },
  medium: { ring: '#8A6A12', arc: '#B8933E', glyph: '#FFFFFF', fill: 'partial', sweep: 0.55 },
  low:    { ring: '#7A8699', arc: '#AEB8C6', glyph: '#5A6472', fill: 'outline', sweep: 0.22 },
};

function arcPath(cx, cy, r, sweep) {
  const start = -Math.PI / 2;
  const end = start + sweep * Math.PI * 2;
  const x1 = cx + r * Math.cos(start);
  const y1 = cy + r * Math.sin(start);
  const x2 = cx + r * Math.cos(end);
  const y2 = cy + r * Math.sin(end);
  const large = sweep > 0.5 ? 1 : 0;
  if (sweep >= 0.999) {
    return `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.001} ${cy - r}`;
  }
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
}

export default function Seal({ tier = 'high', size = 40, className = '', title }) {
  const s = TIER_STYLE[tier] || TIER_STYLE.high;
  const cx = 32, cy = 32, rOuter = 29, rArc = 23;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={`seal-mark seal-mark-${tier} ${className}`}
      role={title ? 'img' : 'presentation'}
      aria-label={title}
    >
      {title && <title>{title}</title>}
      <circle cx={cx} cy={cy} r={rOuter} fill="var(--paper)" stroke={s.ring} strokeWidth="1.5" />
      <circle cx={cx} cy={cy} r={rOuter - 4.5} fill="none" stroke={s.ring} strokeWidth="1" strokeDasharray="1.5 3" opacity="0.55" />
      <path
        d={arcPath(cx, cy, rArc, s.sweep)}
        fill="none"
        stroke={s.arc}
        strokeWidth="5"
        strokeLinecap="round"
      />
      {s.fill === 'outline' ? (
        <circle cx={cx} cy={cy} r="9" fill="none" stroke={s.glyph} strokeWidth="2.5" />
      ) : (
        <>
          <circle cx={cx} cy={cy} r="14" fill={s.arc} />
          <path
            d="M23.5 33.5 L29.5 39.5 L41 24.5"
            fill="none"
            stroke={s.glyph}
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </>
      )}
    </svg>
  );
}
