/**
 * Settings Page
 */

export default function Settings() {
  return (
    <div className="container-main">
      <h2 className="text-3xl font-bold mb-6">Settings</h2>
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Application Settings</h3>
        <form className="space-y-4">
          <div>
            <label className="label">App Name</label>
            <input type="text" className="input" placeholder="BillOps" />
          </div>
          <div>
            <label className="label">Timezone</label>
            <select className="input">
              <option>UTC</option>
              <option>EST</option>
              <option>CST</option>
              <option>MST</option>
              <option>PST</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary">
            Save Changes
          </button>
        </form>
      </div>
    </div>
  );
}
