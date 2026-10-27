import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from './BRDViewer.module.css';

export default function BRDViewer({ content }) {
  return (
    <div className={styles.document}>
      <div className={styles.docHeader}>
        <span className={styles.docIcon}>📋</span>
        <span className={styles.docTitle}>Business Requirements Document</span>
      </div>
      <div className={styles.body}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
