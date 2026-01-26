import './styles/global.css';

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>BillOps</h1>
        <p className="app-subtitle">Billing, invoicing, and time tracking made simple.</p>
      </header>
      <main className="app-main">
        <section className="card">
          <h2>Getting Started</h2>
          <ol>
            <li>Set your API base URL in src/lib/api.ts</li>
            <li>Add feature modules under src/features</li>
            <li>Wire routes in src/routes</li>
          </ol>
        </section>
        <section className="card">
          <h2>Project Structure</h2>
          <ul>
            <li>Components: shared UI building blocks</li>
            <li>Features: domain-specific flows</li>
            <li>Services: API clients and adapters</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

export default App;
