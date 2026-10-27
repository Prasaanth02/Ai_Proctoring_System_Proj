import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import BRDOptions from '../components/BRDOptions';
import GenerateButton from '../components/GenerateButton';
import ProcessingState from '../components/ProcessingState';
import BRDViewer from '../components/BRDViewer';
import ResultActions from '../components/ResultActions';
import { generateBRD } from '../services/api';
import styles from './BRDGenerator.module.css';

const STATES = { EMPTY: 'EMPTY', FILE_SELECTED: 'FILE_SELECTED', PROCESSING: 'PROCESSING', SUCCESS: 'SUCCESS', ERROR: 'ERROR' };

export default function BRDGenerator() {
  const [file, setFile] = useState(null);
  const [options, setOptions] = useState({ style: 'Professional', format: 'Structured BRD' });
  const [status, setStatus] = useState(STATES.EMPTY);
  const [brd, setBrd] = useState('');
  const [filename, setFilename] = useState('');
  const [error, setError] = useState(null);

  function handleFile(f) {
    setFile(f);
    setStatus(f ? STATES.FILE_SELECTED : STATES.EMPTY);
    setError(null);
  }

  function handleError(msg) {
    setError(msg);
    if (msg) setStatus(STATES.ERROR);
  }

  async function handleGenerate() {
    if (!file) { handleError('Please select a file before generating.'); return; }
    setStatus(STATES.PROCESSING);
    setError(null);
    try {
      const result = await generateBRD(file);
      setBrd(result.brd);
      setFilename(result.filename);
      setStatus(STATES.SUCCESS);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred. Please try again.');
      setStatus(STATES.ERROR);
    }
  }

  function handleReset() {
    setFile(null);
    setBrd('');
    setFilename('');
    setError(null);
    setStatus(STATES.EMPTY);
  }

  const isProcessing = status === STATES.PROCESSING;
  const isSuccess = status === STATES.SUCCESS;

  return (
    <main className={styles.main}>
      <div className={styles.container}>

        {/* Hero */}
        <div className={styles.hero}>
          <h1 className={styles.heroTitle}>AI-Powered BRD Generator</h1>
          <p className={styles.heroSub}>
            Upload your business document and get a structured, professional
            Business Requirements Document in seconds.
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className={styles.errorBanner}>
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}

        {/* Upload + options — hidden during processing/success */}
        {!isProcessing && !isSuccess && (
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Upload Document</h2>
            <FileUpload file={file} onFile={handleFile} onError={handleError} />
          </div>
        )}

        {!isProcessing && !isSuccess && (
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>Configuration</h2>
            <BRDOptions options={options} onChange={setOptions} />
          </div>
        )}

        {!isProcessing && !isSuccess && (
          <GenerateButton onClick={handleGenerate} disabled={!file} />
        )}

        {/* Processing */}
        {isProcessing && <ProcessingState />}

        {/* Result */}
        {isSuccess && (
          <>
            <ResultActions brd={brd} filename={filename} onReset={handleReset} />
            <BRDViewer content={brd} />
          </>
        )}

      </div>
    </main>
  );
}
