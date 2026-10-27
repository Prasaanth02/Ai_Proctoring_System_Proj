import { useEffect, useState } from 'react';
import styles from './ProcessingState.module.css';

const STEPS = [
  'Analyzing document...',
  'Extracting requirements...',
  'Generating BRD...',
];

export default function ProcessingState() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStep((s) => (s + 1) % STEPS.length), 2800);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={styles.wrapper}>
      <div className={styles.spinner} />
      <p className={styles.message}>{STEPS[step]}</p>
      <p className={styles.sub}>This may take a moment depending on document size.</p>
    </div>
  );
}
