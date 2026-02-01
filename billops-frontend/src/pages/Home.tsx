/**
 * Home Page
 */

export default function Home() {
  return (
    <div className="container-main">
      <h2 className="text-3xl font-bold mb-6">Welcome to BillOps</h2>
      <div className="grid-auto">
        <div className="card">
          <h3 className="text-xl font-semibold mb-2">Quick Start</h3>
          <p className="text-gray-600">Get started by exploring the dashboard or managing invoices.</p>
        </div>
        <div className="card">
          <h3 className="text-xl font-semibold mb-2">Time Tracking</h3>
          <p className="text-gray-600">Capture and track billable hours for your projects.</p>
        </div>
        <div className="card">
          <h3 className="text-xl font-semibold mb-2">Reports</h3>
          <p className="text-gray-600">Generate comprehensive billing and time reports.</p>
        </div>
      </div>
    </div>
  );
}
