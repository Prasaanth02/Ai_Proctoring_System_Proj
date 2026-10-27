import { useState } from 'react';
import styles from './ResultActions.module.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ResultActions({ brd, filename, onReset }) {
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);

  async function handleDownloadPDF() {
    setDownloading(true);
    try {
      const form = new FormData();
      form.append('brd', brd);
      form.append('filename', filename);

      const res = await fetch(`${API_BASE}/download-pdf`, {
        method: 'POST',
        body: form,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'PDF generation failed');
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `BRD_${filename.replace(/\.[^.]+$/, '')}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloading(false);
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(brd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className={styles.actions}>
      <button className={styles.primary} onClick={handleDownloadPDF} disabled={downloading}>
        {downloading ? '⏳ Generating PDF...' : '⬇ Download PDF'}
      </button>
      <button className={styles.secondary} onClick={handleCopy}>
        {copied ? '✓ Copied!' : '⎘ Copy'}
      </button>
      <button className={styles.ghost} onClick={onReset}>
        ↺ Generate New BRD
      </button>
    </div>
  );
}
