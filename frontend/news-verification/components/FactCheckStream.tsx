// FactCheckStream.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const FactCheckStream = ({ article }) => {
  const [status, setStatus] = useState('idle');
  const [messages, setMessages] = useState([]);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!article) return;
    
    setStatus('processing');
    setMessages([]);
    setProgress(0);
    
    // Create EventSource for Server-Sent Events
    const eventSource = new EventSource(
      `/api/factcheck/stream?article=${encodeURIComponent(article)}`
    );
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received update:", data);
        
        // Add message to our list
        setMessages((prev) => [...prev, data]);
        
        // Track progress for progress bar - estimate based on status messages
        if (data.status === 'processing') {
          if (data.data?.current_chunk && data.data?.total_chunks) {
            // If we have chunk information, use it for progress
            const percent = Math.round((data.data.current_chunk / data.data.total_chunks) * 80);
            setProgress(20 + percent); // Start at 20%, end at 100%
          } else {
            // Otherwise increment progress by a small amount
            setProgress((prev) => Math.min(prev + 2, 90));
          }
        }
        
        // Final result data
        if (data.status === 'completed' && data.data?.result_data) {
          setResult(data.data.result_data);
          setProgress(100);
        }
        
        // Update status
        if (data.status === 'completed' || data.status === 'done') {
          setStatus('completed');
          setProgress(100);
          eventSource.close();
        } else if (data.status === 'error') {
          setStatus('error');
          eventSource.close();
        } else if (data.status === 'starting') {
          setProgress(10);
        }
      } catch (error) {
        console.error("Error parsing event data:", error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error("EventSource error:", error);
      setStatus('error');
      eventSource.close();
    };
    
    return () => {
      eventSource.close();
    };
  }, [article]);

  return (
    <div className="fact-check-container">
      <div className="progress-container">
        <div 
          className={`progress-bar ${status === 'error' ? 'error' : ''}`}
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      
      <div className="status-display">
        {status === 'processing' && <span>Processing... {progress}%</span>}
        {status === 'completed' && <span>Analysis Complete!</span>}
        {status === 'error' && <span>Error processing article</span>}
      </div>
      
      <div className="messages-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.status}`}>
            <span className="timestamp">{new Date().toLocaleTimeString()}</span>
            <span className="message-text">{msg.message}</span>
          </div>
        ))}
      </div>
      
      {result && (
        <div className="results-container">
          <h3>Fact Check Results</h3>
          
          {result.sentiment_analysis && (
            <div className="sentiment-section">
              <h4>Sentiment Analysis</h4>
              <p>
                <strong>{result.sentiment_analysis.reasoning}</strong> 
                (Score: {result.sentiment_analysis.score.toFixed(2)})
              </p>
            </div>
          )}
          
          {result.summary && (
            <div className="summary-section">
              <h4>Summary</h4>
              <p>{result.summary}</p>
            </div>
          )}
          
          {result.fact_checks && result.fact_checks.length > 0 && (
            <div className="fact-checks-section">
              <h4>Fact Checks</h4>
              {result.fact_checks.map((check, index) => (
                <div key={index} className="fact-check-item">
                  <p className="statement"><strong>Statement:</strong> {check.statement}</p>
                  <p><strong>Search Topic:</strong> {check.search_topic}</p>
                  {check.articles && check.articles.length > 0 ? (
                    <div className="articles">
                      <p><strong>Supporting Articles:</strong> {check.articles.length} found</p>
                      <ul>
                        {check.articles.map((article, idx) => (
                          <li key={idx}>
                            <a href={article.url} target="_blank" rel="noopener noreferrer">
                              {article.title || 'Untitled Article'}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <p><strong>No supporting articles found</strong></p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FactCheckStream;