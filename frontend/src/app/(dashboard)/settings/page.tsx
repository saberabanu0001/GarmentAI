export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow-md">
      <h1 className="text-xl font-bold text-zinc-900">Settings</h1>
      <p className="mt-2 text-sm text-zinc-600">
        Tenant, API URL, and role defaults will live here. Use environment and
        server config — avoid embedding secrets in the client bundle.
      </p>
    </div>
  );
}
