import { useRef, useState } from 'react';
import styles from './FileUpload.module.css';

const SUPPORTED = ['.pdf', '.txt'];
const MAX_MB = 20;

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({ file, onFile, onError }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function validate(f) {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!SUPPORTED.includes(ext)) {
      onError(`Unsupported file type "${ext}". Please upload a PDF or TXT file.`);
      return false;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      onError(`File exceeds ${MAX_MB} MB limit.`);
      return false;
    }
    return true;
  }

  function handleSelect(f) {
    if (f && validate(f)) { onError(null); onFile(f); }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleSelect(f);
  }

  return (
    <div className={styles.wrapper}>
      {!file ? (
        <div
          className={`${styles.dropzone} ${dragging ? styles.dragging : ''}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <span className={styles.icon}>📄</span>
          <p className={styles.primary}>Drag &amp; Drop your business document here</p>
          <p className={styles.or}>or</p>
          <button type="button" className={styles.browse}>Browse Files</button>
          <p className={styles.hint}>Supported formats: PDF, TXT &nbsp;·&nbsp; Max {MAX_MB} MB</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt"
            style={{ display: 'none' }}
            onChange={(e) => handleSelect(e.target.files[0])}
          />
        </div>
      ) : (
        <div className={styles.fileCard}>
          <span className={styles.fileIcon}>{file.name.endsWith('.pdf') ? '📕' : '📝'}</span>
          <div className={styles.fileMeta}>
            <span className={styles.fileName}>{file.name}</span>
            <span className={styles.fileInfo}>
              {file.name.split('.').pop().toUpperCase()} &nbsp;·&nbsp; {formatSize(file.size)}
            </span>
          </div>
          <button
            type="button"
            className={styles.remove}
            onClick={() => { onFile(null); onError(null); }}
            title="Remove file"
          >✕</button>
        </div>
      )}
    </div>
  );
}
