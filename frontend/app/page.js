'use client'; 

import Head from 'next/head';
import { useState, useEffect, useMemo } from 'react';
import { Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip, // Ensure Tooltip is registered
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip, // Make sure Tooltip is here
  Legend,
  ArcElement
);

export default function HomePage() {
  const [productUrl, setProductUrl] = useState('');
  const [reviews, setReviews] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sheetUrl, setSheetUrl] = useState('');

  const sentimentCounts = useMemo(() => {
    if (reviews.length === 0) {
      return { Positive: 0, Negative: 0, Neutral: 0 };
    }
    return reviews.reduce(
      (acc, review) => {
        acc[review.sentiment_label] = (acc[review.sentiment_label] || 0) + 1;
        return acc;
      },
      { Positive: 0, Negative: 0, Neutral: 0 }
    );
  }, [reviews]);

  const handleScrape = async (e) => {
    e.preventDefault(); 
    if (!productUrl.trim()) {
      setError("Please enter a product URL.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setReviews([]);
    setSheetUrl('');

    try {
      const response = await fetch('http://localhost:8000/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_url: productUrl }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || `HTTP error! Status: ${response.status}`);
      }
      setReviews(result.data || []);
      setSheetUrl(result.sheet_url || '');
      if (!result.data || result.data.length === 0) {
        setError("No reviews were returned. The product might have no reviews, or scraper selectors need an update.");
      }
    } catch (e) {
      console.error("Scraping error:", e);
      setError(e.message || "An unexpected error occurred.");
      setReviews([]);
    } finally {
      setIsLoading(false);
    }
  };

  const totalReviews = reviews.length;

  const chartData = useMemo(() => ({
    labels: Object.keys(sentimentCounts),
    datasets: [
      {
        label: 'Sentiment Count', // Changed for clarity in tooltip
        data: Object.values(sentimentCounts),
        backgroundColor: [
          'rgba(75, 192, 192, 0.7)',
          'rgba(255, 99, 132, 0.7)',
          'rgba(201, 203, 207, 0.7)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(201, 203, 207, 1)',
        ],
        borderWidth: 1,
        hoverOffset: 4, // Makes segment pop out slightly on hover
      },
    ],
  }), [sentimentCounts]);

  // --- Enhanced Chart Options ---
  const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { // Ensure animations are on and potentially customize
      duration: 1000, // Animation duration in ms
      easing: 'easeInOutQuart', // Easing function
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          padding: 20, // Add some padding to legend items
          font: {
            size: 14,
          }
        },
        onClick: (e, legendItem, legend) => { // Default behavior
          const index = legendItem.datasetIndex;
          const ci = legend.chart;
          if (ci.isDatasetVisible(index)) {
              ci.hide(index);
              legendItem.hidden = true;
          } else {
              ci.show(index);
              legendItem.hidden = false;
          }
          // For pie/doughnut, toggle visibility of the segment
          if (ci.config.type === 'pie' || ci.config.type === 'doughnut') {
            ci.toggleDataVisibility(legendItem.index);
            ci.update();
          }
        }
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)', // Darker tooltip
        titleFont: { size: 16 },
        bodyFont: { size: 14 },
        padding: 10,
        cornerRadius: 4,
        displayColors: true, // Show color box in tooltip
        callbacks: { // Custom tooltip content
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null && context.chart.config.type !== 'pie' && context.chart.config.type !== 'doughnut') {
              label += context.parsed.y;
            }
            if (context.parsed !== null && (context.chart.config.type === 'pie' || context.chart.config.type === 'doughnut')) {
              const value = context.parsed;
              const percentage = totalReviews > 0 ? ((value / totalReviews) * 100).toFixed(1) : 0;
              label += `${value} (${percentage}%)`;
            }
            return label;
          }
        }
      },
    },
  };

  const barChartOptions = {
    ...commonChartOptions,
    scales: { // Specific to bar chart
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 5, // Adjust step size based on your data range
        }
      }
    },
    plugins: {
      ...commonChartOptions.plugins,
      title: {
        display: true,
        text: 'Sentiment Counts (Bar)',
        font: { size: 18 },
        padding: { top: 10, bottom: 20 }
      },
    },
  };

  const pieChartOptions = {
    ...commonChartOptions,
    plugins: {
      ...commonChartOptions.plugins,
      title: {
        display: true,
        text: 'Sentiment Proportions (Pie)',
        font: { size: 18 },
        padding: { top: 10, bottom: 20 }
      },
    },
  };
  // --- End Enhanced Chart Options ---


  // Inline styles (consider moving to a CSS module for larger apps)
  const styles = { // Your existing styles here...
    container: { fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '20px auto', padding: '20px', background: '#f9f9f9', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' },
    header: { textAlign: 'center', color: '#333', marginBottom: '30px' },
    form: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '30px', flexWrap: 'wrap' },
    input: { flexGrow: 1, padding: '12px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '16px' },
    button: { padding: '12px 20px', backgroundColor: '#0070f3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px', transition: 'background-color 0.2s' },
    buttonDisabled: { backgroundColor: '#ccc', cursor: 'not-allowed' },
    error: { color: 'red', marginBottom: '15px', textAlign: 'center', background: '#ffebee', padding: '10px', borderRadius: '4px' },
    sheetLink: { display: 'block', textAlign: 'center', marginBottom: '20px', color: '#0070f3', fontWeight: 'bold' },
    tableContainer: { overflowX: 'auto', marginBottom: '30px' },
    table: { width: '100%', borderCollapse: 'collapse', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
    th: { backgroundColor: '#0070f3', color: 'white', padding: '12px', textAlign: 'left', borderBottom: '2px solid #0056b3' },
    td: { padding: '10px', border: '1px solid #eee', textAlign: 'left', background: 'white' },
    sentimentCellPositive: { color: 'green', fontWeight: 'bold' },
    sentimentCellNegative: { color: 'red', fontWeight: 'bold' },
    sentimentCellNeutral: { color: 'gray' },
    chartsContainer: { display: 'flex', flexDirection: 'column', gap: '30px', alignItems: 'center', marginBottom: '30px' }, // Changed to column for better responsiveness
    chartWrapper: { width: '100%', maxWidth: '700px', height: '400px', background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }, // Increased max-width
    noReviews: { textAlign: 'center', color: '#777', marginTop: '20px', fontSize: '18px' },
    loader: { textAlign: 'center', fontSize: '20px', color: '#0070f3', margin: '30px 0' }
  };

  const getSentimentStyle = (label) => {
    if (label === 'Positive') return styles.sentimentCellPositive;
    if (label === 'Negative') return styles.sentimentCellNegative;
    return styles.sentimentCellNeutral;
  };

  return (
    <>
      <Head>
        <title>Product Review Sentiment Scraper</title>
        <meta name="description" content="Scrape and analyze product reviews" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div style={styles.container}>
        <header>
          <h1 style={styles.header}>Product Review Sentiment Scraper</h1>
        </header>

        <form onSubmit={handleScrape} style={styles.form}>
          <input
            type="url"
            value={productUrl}
            onChange={(e) => setProductUrl(e.target.value)}
            placeholder="Enter Daraz.pk Product URL"
            style={styles.input}
            required
          />
          <button type="submit" disabled={isLoading} style={{...styles.button, ...(isLoading && styles.buttonDisabled)}}>
            {isLoading ? 'Scraping...' : 'Scrape Reviews'}
          </button>
        </form>

        {isLoading && <div style={styles.loader}>Scraping data, please wait... This might take a moment.</div>}
        {error && <p style={styles.error}>{error}</p>}
        
        {sheetUrl && !isLoading && (
          <p style={styles.sheetLink}>
            Data saved to Google Sheet: <a href={sheetUrl} target="_blank" rel="noopener noreferrer">{sheetUrl}</a>
          </p>
        )}

        {reviews.length > 0 && !isLoading && (
          <>
            <h2 style={{ textAlign: 'center', color: '#333', marginBottom: '20px' }}>Scraped Reviews ({reviews.length})</h2>
            <div style={styles.tableContainer}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Product Name</th>
                    <th style={styles.th}>Review Text</th>
                    <th style={styles.th}>Rating</th>
                    <th style={styles.th}>Sentiment</th>
                    <th style={styles.th}>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {reviews.map((review, index) => (
                    <tr key={index}>
                      <td style={styles.td}>{review.product_name}</td>
                      <td style={styles.td}>{review.review_text}</td>
                      <td style={styles.td}>{review.rating}</td>
                      <td style={{...styles.td, ...getSentimentStyle(review.sentiment_label)}}>
                        {review.sentiment_label}
                      </td>
                      <td style={styles.td}>{review.sentiment_score?.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h2 style={{ textAlign: 'center', color: '#333', marginTop: '40px', marginBottom: '10px' }}>Sentiment Distribution</h2>
            <div style={styles.chartsContainer}>
              <div style={styles.chartWrapper}>
                <h3 style={{textAlign: 'center'}}>Bar Chart</h3>
                <Bar data={chartData} options={barChartOptions} />
              </div>
              <div style={styles.chartWrapper}>
                <h3 style={{textAlign: 'center'}}>Pie Chart</h3>
                <Pie data={chartData} options={pieChartOptions} />
              </div>
            </div>
          </>
        )}
        {reviews.length === 0 && !isLoading && !error && productUrl && (
             <p style={styles.noReviews}>No reviews to display. Try scraping a product with reviews.</p>
        )}
      </div>
    </>
  );
}