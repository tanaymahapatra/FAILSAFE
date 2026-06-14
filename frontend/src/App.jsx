import React, { useState } from 'react';
import './App.css';

function App() {
  // ==========================================
  // STATE MANAGEMENT
  // ==========================================
  // Authentication & Session
  const [token, setToken] = useState(null);
  const [currentUser, setCurrentUser] = useState('');
  const [userRole, setUserRole] = useState('');
  const [usernameInput, setUsernameInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');

  // Pipeline Configuration
  const [predictionType, setPredictionType] = useState('full');
  const [uploadType, setUploadType] = useState('full');
  const [teacherFilter, setTeacherFilter] = useState('');

  // UI & Data State
  const [uploadFile, setUploadFile] = useState(null);
  const [status, setStatus] = useState({ message: '', type: '' }); // type: 'error' | 'success' | 'info'
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  // ==========================================
  // API CALLS
  // ==========================================
  const showStatus = (message, type = 'info') => {
    setStatus({ message, type });
    setTimeout(() => setStatus({ message: '', type: '' }), 5000); // Auto-clear after 5s
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formData = new URLSearchParams();
    formData.append('username', usernameInput);
    formData.append('password', passwordInput);

    try {
      const response = await fetch('http://127.0.0.1:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        setToken(data.access_token);
        setCurrentUser(data.username);
        setUserRole(data.role);
        showStatus(`Welcome back, ${data.username}!`, 'success');
      } else {
        showStatus(data.detail || 'Login failed. Check credentials.', 'error');
      }
    } catch (err) {
      showStatus('Server connection failed. Is the backend running?', 'error');
    }
    setLoading(false);
  };

  const handleUpload = async (customEndpoint = null) => {
    if (!uploadFile) {
      showStatus('Please select a CSV file first.', 'error');
      return;
    }
    setLoading(true);

    const endpoint = customEndpoint || (uploadType === 'full' ? 'upload_grades' : 'upload_grades_g1');
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const response = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      const data = await response.json();

      if (response.ok) {
        showStatus(data.message, 'success');
        setUploadFile(null);
        document.getElementById('file-upload-input').value = ''; // Reset file input
      } else {
        showStatus(`Upload Error: ${JSON.stringify(data.detail)}`, 'error');
      }
    } catch (err) {
      showStatus('Upload failed. Check your server connection.', 'error');
    }
    setLoading(false);
  };

  const handlePredict = async () => {
    setLoading(true);
    setReport(null); // Clear previous report

    let endpoint = 'predict_risk';
    if (predictionType === 'demo_only') endpoint = 'predict_risk_demo_only';
    else if (predictionType === 'demo_g1') endpoint = 'predict_risk_demo_g1';

    let url = `http://127.0.0.1:8000/${endpoint}`;

    if (userRole === 'HOD' && teacherFilter !== '' && predictionType === 'full') {
      url += `?teacher_filter=${teacherFilter}`;
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await response.json();

      if (response.ok) {
        setReport(data);
        showStatus('Risk analysis completed successfully.', 'success');
      } else {
        showStatus(data.detail || 'Prediction failed.', 'error');
      }
    } catch (err) {
      showStatus('Failed to run analysis. Server error.', 'error');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setToken(null);
    setReport(null);
    setUsernameInput('');
    setPasswordInput('');
    setStatus({ message: '', type: '' });
  };

  // ==========================================
  // HELPER COMPONENTS
  // ==========================================
  const getRiskColor = (probability) => {
    if (probability >= 75) return '#EF4444'; // Red
    if (probability >= 50) return '#F59E0B'; // Orange
    return '#3B82F6'; // Blue for lower flags
  };

  // ==========================================
  // RENDER: LOGIN VIEW
  // ==========================================
  if (!token) {
    return (
      <div className="login-wrapper">
        <div className="login-container">
          <div className="login-header">
            <h2>FAILSAFE</h2>
            <p>Student Risk Intelligence Platform</p>
          </div>
          <form onSubmit={handleLogin} className="login-form">
            <div className="input-group">
              <label>Username</label>
              <input type="text" value={usernameInput} onChange={(e) => setUsernameInput(e.target.value)} required placeholder="Enter your ID" />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input type="password" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)} required placeholder="••••••••" />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Authenticating...' : 'Sign In Securely'}
            </button>
          </form>
          {status.message && <p className={`message ${status.type}`}>{status.message}</p>}
        </div>
      </div>
    );
  }

  // ==========================================
  // RENDER: DASHBOARD VIEW
  // ==========================================
  return (
    <div className="container dashboard">
      {/* Navbar */}
      <header className="dashboard-header">
        <div className="brand">
          <h2>FAILSAFE Analytics</h2>
          <span className="role-badge">{userRole} Workspace</span>
        </div>
        <div className="user-controls">
          <p className="user-badge">Logged in as <strong>{currentUser}</strong></p>
          <button onClick={handleLogout} className="btn-logout">Sign Out</button>
        </div>
      </header>

      {/* Global Status Notifications */}
      {status.message && (
        <div className={`status-banner ${status.type}`}>
          {status.message}
        </div>
      )}

      {/* Main Control Panel (Grid Layout) */}
      <div className="control-panel">

        {/* Left Column: Data Management */}
        <div className="card data-card">
          <div className="card-header">
            <h3>Data Management</h3>
            <span className="icon">📂</span>
          </div>
          <p className="helper-text">Ensure your datasets are up-to-date before running predictions.</p>

          {userRole === 'HOD' && (
            <div className="upload-block">
              <label>Master Demographics Database (.csv)</label>
              <input id="file-upload-input" type="file" accept=".csv" onChange={(e) => setUploadFile(e.target.files[0])} />
              <button onClick={() => handleUpload('Upload_demographics')} disabled={loading}>
                {loading ? 'Syncing...' : 'Upload Demographics'}
              </button>
            </div>
          )}

          {userRole === 'Teacher' && (
            <div className="upload-block">
              <label>Academic Grades Format</label>
              <select value={uploadType} onChange={(e) => setUploadType(e.target.value)}>
                <option value="full">End of Year (G1 + G2)</option>
                <option value="g1_only">Mid-Year Checkpoint (G1 Only)</option>
              </select>
              <input id="file-upload-input" type="file" accept=".csv" onChange={(e) => setUploadFile(e.target.files[0])} />
              <button onClick={() => handleUpload()} disabled={loading}>
                {loading ? 'Processing...' : 'Upload Grades Data'}
              </button>
            </div>
          )}
        </div>

        {/* Right Column: AI Model Config */}
        <div className="card predict-card">
          <div className="card-header">
            <h3>Intelligence Pipeline</h3>
            <span className="icon">🧠</span>
          </div>
          <p className="helper-text">Select the AI model architecture based on available data.</p>

          <div className="filter-group">
            <label>Model Architecture</label>
            <select value={predictionType} onChange={(e) => setPredictionType(e.target.value)}>
              <option value="full">Full Context (Demographics + G1 + G2)</option>
              <option value="demo_g1">Early Warning (Demographics + G1)</option>
              <option value="demo_only">Baseline Risk (Demographics Only)</option>
            </select>
          </div>

          {userRole === 'HOD' && predictionType === 'full' && (
            <div className="filter-group">
              <label>Filter Target Audience</label>
              <select value={teacherFilter} onChange={(e) => setTeacherFilter(e.target.value)}>
                <option value="">Institution Wide (All Teachers)</option>
                <option value="t1">Classroom: t1</option>
                <option value="t2">Classroom: t2</option>
              </select>
            </div>
          )}

          <button className="btn-predict" onClick={handlePredict} disabled={loading}>
            {loading ? 'Executing AI Models...' : 'Run Risk Analysis'}
          </button>
        </div>
      </div>

      {/* Results Section */}
      <div className="report-section card">
        <h3>Analysis Results</h3>

        {/* State 1: No Report Generated Yet */}
        {!report && !loading && (
          <div className="empty-state">
            <p>No active report. Configure the pipeline above and click "Run Risk Analysis" to generate insights.</p>
          </div>
        )}

        {/* State 2: Loading State */}
        {loading && !report && (
          <div className="empty-state loading-state">
            <div className="spinner"></div>
            <p>Analyzing student profiles...</p>
          </div>
        )}

        {/* State 3: Report Successfully Generated */}
        {report && (
          <>
            <div className="report-metadata">
              <div className="meta-item">
                <span className="label">Scope</span>
                <span className="value">{report.Viewing_Teacher_Data}</span>
              </div>
              <div className="meta-item">
                <span className="label">Evaluated</span>
                <span className="value">{report.Total_Students_Evaluated} Students</span>
              </div>
              <div className="meta-item warning">
                <span className="label">Flagged At-Risk</span>
                <span className="value">{report.At_Risk_Count} Students</span>
              </div>
            </div>

            {report.At_Risk_Students && report.At_Risk_Students.length > 0 ? (
              <div className="table-responsive">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Student ID</th>
                      <th>Assigned To</th>
                      <th>Risk Probability</th>
                      <th>Primary Risk Factors (SHAP Analysis)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.At_Risk_Students.map((student, index) => (
                      <tr key={index}>
                        <td className="fw-bold">{student.Student_ID}</td>
                        <td>{student.Teacher_ID || 'Unassigned'}</td>
                        <td>
                          <span
                            className="risk-badge"
                            style={{ backgroundColor: getRiskColor(student.Risk_Probability) }}
                          >
                            {student.Risk_Probability}%
                          </span>
                        </td>
                        <td>
                          <ul className="shap-list">
                            {student.Top_Reasons && student.Top_Reasons.map((reason, i) => (
                              <li key={i}>{reason}</li>
                            ))}
                          </ul>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state success-state">
                <h3>✅ All Clear</h3>
                <p>No students in this dataset meet the high-risk threshold.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default App;