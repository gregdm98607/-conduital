// Minimal test version of App.tsx
// Use this to test if basic React rendering works

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          ✅ React is Working!
        </h1>
        <p className="text-gray-600">
          If you see this, the basic setup is correct.
        </p>
        <p className="text-sm text-gray-500 mt-4">
          Now check the browser console for any errors.
        </p>
      </div>
    </div>
  );
}

export default App;
