import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { InboxPage } from './pages/InboxPage';
import { Areas } from './pages/Areas';
import { AreaDetail } from './pages/AreaDetail';
import { Projects } from './pages/Projects';
import { ProjectDetail } from './pages/ProjectDetail';
import { AllTasks } from './pages/AllTasks';
import { NextActions } from './pages/NextActions';
import { DailyDashboard } from './pages/DailyDashboard';
import { WeeklyReviewPage } from './pages/WeeklyReviewPage';
import { SomedayMaybe } from './pages/SomedayMaybe';
import { Settings } from './pages/Settings';
import { MemoryPage } from './pages/MemoryPage';
import { LoginPage } from './pages/LoginPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public route - Login page */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected routes - wrapped in Layout */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="inbox" element={<InboxPage />} />
                <Route path="areas" element={<Areas />} />
                <Route path="areas/:id" element={<AreaDetail />} />
                <Route path="projects" element={<Projects />} />
                <Route path="projects/:id" element={<ProjectDetail />} />
                <Route path="tasks" element={<AllTasks />} />
                <Route path="next-actions" element={<NextActions />} />
                <Route path="daily" element={<DailyDashboard />} />
                <Route path="someday-maybe" element={<SomedayMaybe />} />
                <Route path="weekly-review" element={<WeeklyReviewPage />} />
                <Route path="settings" element={<Settings />} />
                <Route path="memory" element={<MemoryPage />} />
                <Route path="onboarding" element={<OnboardingPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
