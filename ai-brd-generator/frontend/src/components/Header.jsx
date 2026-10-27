import styles from './Header.module.css';

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⚡</span>
          <span className={styles.logoText}>BRD<span className={styles.logoAccent}>AI</span></span>
        </div>
        <p className={styles.tagline}>Generate structured Business Requirements Documents from your business information.</p>
      </div>
    </header>
  );
}
