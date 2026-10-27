import styles from './GenerateButton.module.css';

export default function GenerateButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      className={styles.btn}
      onClick={onClick}
      disabled={disabled}
    >
      <span className={styles.icon}>✦</span>
      Generate BRD
    </button>
  );
}
