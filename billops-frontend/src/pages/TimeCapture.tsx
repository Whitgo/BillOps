/**
 * Time Capture Page
 */

export default function TimeCapture() {
  return (
    <div className="container-main">
      <div className="flex-between mb-6">
        <h2 className="text-3xl font-bold">Time Capture</h2>
        <button className="btn btn-primary">+ Log Time</button>
      </div>
      <div className="card">
        <p className="text-gray-600">No time entries yet. Start tracking billable hours.</p>
      </div>
    </div>
  );
}
