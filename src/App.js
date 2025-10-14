import React from "react";
import "./App.css";

function App() {
  return (
    <div className="app-container">
      <h1>📊 Donor Data Analysis Dashboard</h1>

      {/* Section 1: File Upload */}
      <section className="section">
        <h2>1️⃣ Upload Donor Data</h2>
        <p>Upload your donor data file (CSV or Excel format).</p>
        <input type="file" accept=".csv, .xlsx" />
      </section>

      {/* Section 2: Data Preview */}
      <section className="section">
        <h2>2️⃣ Data Preview</h2>
        <p>A quick look at your uploaded data will appear here once uploaded.</p>
        <div className="placeholder-box">[Data preview placeholder]</div>
      </section>

      {/* Section 3: Summary Statistics */}
      <section className="section">
        <h2>3️⃣ Summary Statistics</h2>
        <p>Key statistics will be displayed here once implemented.</p>
        <div className="placeholder-box">[Statistics placeholder]</div>
      </section>

      {/* Section 4: Data Visualizations */}
      <section className="section">
        <h2>4️⃣ Data Visualizations</h2>
        <p>Charts and graphs will be generated here based on your data.</p>
        <div className="placeholder-box">[Visualizations placeholder]</div>
      </section>

      <footer>
        <hr />
        <p className="footer">Built with ❤️ using React</p>
      </footer>
    </div>
  );
}

export default App;

