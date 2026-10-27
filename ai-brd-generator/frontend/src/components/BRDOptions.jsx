import styles from './BRDOptions.module.css';

const STYLES = ['Professional', 'Detailed', 'Concise'];
const FORMATS = ['Structured BRD', 'Executive-focused BRD'];

export default function BRDOptions({ options, onChange }) {
  return (
    <div className={styles.panel}>
      <div className={styles.group}>
        <label className={styles.label}>
          BRD Style
          <span className={styles.badge}>Future configuration</span>
        </label>
        <div className={styles.pills}>
          {STYLES.map((s) => (
            <button
              key={s}
              type="button"
              className={`${styles.pill} ${options.style === s ? styles.active : ''}`}
              onClick={() => onChange({ ...options, style: s })}
            >{s}</button>
          ))}
        </div>
      </div>

      <div className={styles.group}>
        <label className={styles.label}>
          Output Format
          <span className={styles.badge}>Future configuration</span>
        </label>
        <div className={styles.pills}>
          {FORMATS.map((f) => (
            <button
              key={f}
              type="button"
              className={`${styles.pill} ${options.format === f ? styles.active : ''}`}
              onClick={() => onChange({ ...options, format: f })}
            >{f}</button>
          ))}
        </div>
      </div>
    </div>
  );
}
