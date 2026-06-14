import React, { useState } from 'react';
import './App.css';

function App() {
  // State for Authentication
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // New States for RBAC (Role-Based Access Control)
  const [currentUser, setCurrentUser] = useState('');
  const [userRole, setUserRole] = useState('');
  const [teacherFilter, setTeacherFilter] = useState('');

  // State for Files and UI
  const [uploadFile, setUploadFile] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  // 1. Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch('http://127.0.0.1:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        setToken(data.access_token);
        setCurrentUser(data.username);
        setUserRole(data.role);
        setStatusMessage(`Welcome, ${data.username}!`);
      } else {
        setStatusMessage(data.detail || 'Login failed.');
      }
    } catch (err) {
      setStatusMessage('Error connecting to server.');
    }
    setLoading(false);
  };

  // 2. Handle File Uploads
  const handleUpload = async (endpoint) => {
    if (!uploadFile) {
      setStatusMessage('Please select a file first.');
      return;
    }
    setLoading(true);

    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const response = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        setStatusMessage(data.message);
        setUploadFile(null);
      } else {
        setStatusMessage(`Error: ${JSON.stringify(data.detail)}`);
      }
    } catch (err) {
      setStatusMessage('Upload failed.');
    }
    setLoading(false);
  };

  // 3. Handle Prediction Request
  const handlePredict = async () => {
    setLoading(true);

    let url = 'http://127.0.0.1:8000/predict_risk';
    if (userRole === 'HOD' && teacherFilter !== '') {
      url += `?teacher_filter=${teacherFilter}`;
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      if (response.ok) {
        setReport(data);
        setStatusMessage('Analysis complete!');
      } else {
        setStatusMessage(data.detail || 'Prediction failed.');
      }
    } catch (err) {
      setStatusMessage('Error connecting to server.');
    }
    setLoading(false);
  };

  // 4. Log out
  const handleLogout = () => {
    setToken(null);
    setCurrentUser('');
    setUserRole('');
    setReport(null);
    setStatusMessage('');
    setUsername('');
    setPassword('');
  };

  if (!token) {
    return (
      <div className="container login-container">
        <h2>FAILSAFE Portal</h2>
        <form onSubmit={handleLogin} className="login-form">
          <input
            type="text"
            placeholder="Enter Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Enter Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Authenticating...' : 'Login Securely'}
          </button>
        </form>
        {statusMessage && <p className="message error">{statusMessage}</p>}
      </div>
    );
  }

  return (
    <div className="container dashboard">
      <header>
        <div>
          <h2>FAILSAFE Dashboard</h2>
          <p className="user-badge">Logged in as: <strong>{currentUser}</strong> | Role: <strong>{userRole}</strong></p>
        </div>
        <button onClick={handleLogout} className="btn-logout">Logout</button>
      </header>

      {statusMessage && <div className="status-banner">{statusMessage}</div>}

      <div className="upload-section">
        {userRole === 'HOD' && (
          <div className="card">
            <h3>Demographics Management (HOD Only)</h3>
            <p className="helper-text">Upload the master behavioral/demographic database.</p>
            <input type="file" accept=".csv" onChange={(e) => setUploadFile(e.target.files[0])} />
            <button onClick={() => handleUpload('upload_demographics')} disabled={loading}>
              Upload Demographics
            </button>
          </div>
        )}

        {userRole === 'Teacher' && (
          <div className="card">
            <h3>Grades Management (Teacher Only)</h3>
            <p className="helper-text">Upload your class grades. This data will be securely tagged to your account.</p>
            <input type="file" accept=".csv" onChange={(e) => setUploadFile(e.target.files[0])} />
            <button onClick={() => handleUpload('upload_grades')} disabled={loading}>
              Upload Grades
            </button>
          </div>
        )}
      </div>

      <div className="predict-section card">
        <h3>Risk Analysis Pipeline</h3>

        {userRole === 'HOD' && (
          <div className="filter-group">
            <label>Filter by Teacher Class: </label>
            <select value={teacherFilter} onChange={(e) => setTeacherFilter(e.target.value)}>
              <option value="">All Teachers (Master View)</option>
              <option value="teacher_john">teacher_john</option>
              <option value="teacher_jane">teacher_jane</option>
            </select>
          </div>
        )}

        <button className="btn-predict" onClick={handlePredict} disabled={loading}>
          {loading ? 'Running ML Model...' : 'Execute Risk Prediction'}
        </button>
      </div>

      {report && (
        <div className="report-section card">
          <h3>Generated Risk Report</h3>
          <div className="report-metadata">
            <p>Requested By: <strong>{report.Requested_By}</strong></p>
            <p>Data Scope: <strong style={{ color: '#007bff' }}>{report.Viewing_Teacher_Data}</strong></p>
            <p>Total Evaluated: <strong>{report.Total_Students_Evaluated}</strong></p>
            <p>Flagged At-Risk: <strong className="alert-text">{report.At_Risk_Count}</strong></p>
          </div>

          {report.At_Risk_Students.length > 0 ? (
            <table className="results-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Teacher ID</th> {/* 1. ADDED HEADER HERE */}
                  <th>Status</th>
                  <th>Risk Probability</th>
                </tr>
              </thead>
              <tbody>
                {report.At_Risk_Students.map((student, index) => (
                  <tr key={index}>
                    <td>{student.Student_ID}</td>
                    <td>{student.Teacher_ID}</td>
                    <td className="alert-text">{student.Status}</td>
                    <td>{student.Risk_Probability}%</td>
                  </tr>
                ))}
              </tbody>
            </table>


          ) : (
            <p className="safe-text">✅ No students are currently flagged as high risk in this dataset.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;