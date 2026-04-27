import { useState, useEffect, useMemo } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { api } from '@/services/api';
import { useMomentumSummary } from '@/hooks/useIntelligence';
import { getMomentumColor } from '@/utils/momentum';
import {
  Home,
  Inbox,
  FolderKanban,
  Layers,
  ListTodo,
  CheckSquare,
  CalendarCheck,
  Lightbulb,
  Settings as SettingsIcon,
  Zap,
  CloudCog,
  Target,
  Brain,
  Crosshair,
  Eye,
  Tag,
  Menu,
  X,
} from 'lucide-react';
import { UserMenu } from '@/components/auth/UserMenu';
import { KeyboardShortcutOverlay } from '@/components/common/KeyboardShortcutOverlay';
import { FeedbackWidget } from '@/components/feedback/FeedbackWidget';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  /** Module required for this nav item to be visible */
  requiresModule?: string;
}

interface NavSection {
  label?: string;
  items: NavItem[];
}

// Module-to-nav mapping: which nav items require which modules
const ALL_NAV_SECTIONS: NavSection[] = [
  {
    items: [
      { name: 'Dashboard', href: '/', icon: Home },
      { name: "Today's Focus", href: '/daily', icon: Target },
      { name: 'Inbox', href: '/inbox', icon: Inbox },
    ],
  },
  {
    label: 'Manage',
    items: [
      { name: 'Projects', href: '/projects', icon: FolderKanban },
      { name: 'Areas', href: '/areas', icon: Layers },
      { name: 'Next Actions', href: '/next-actions', icon: ListTodo },
      { name: 'All Tasks', href: '/tasks', icon: CheckSquare },
    ],
  },
  {
    label: 'Horizons',
    items: [
      { name: 'Goals', href: '/goals', icon: Crosshair },
      { name: 'Visions', href: '/visions', icon: Eye },
      { name: 'Contexts', href: '/contexts', icon: Tag },
    ],
  },
  {
    label: 'Review',
    items: [
      { name: 'Someday/Maybe', href: '/someday-maybe', icon: Lightbulb },
      { name: 'Weekly Review', href: '/weekly-review', icon: CalendarCheck },
    ],
  },
  {
    items: [
      { name: 'Memory', href: '/memory', icon: Brain, requiresModule: 'memory_layer' },
      { name: 'Settings', href: '/settings', icon: SettingsIcon },
    ],
  },
];

export function Layout() {
  const location = useLocation();
  const [enabledModules, setEnabledModules] = useState<string[] | null>(null);
  const [appVersion, setAppVersion] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data: momentumSummary } = useMomentumSummary();
  const momentumGlowColor = momentumSummary ? getMomentumColor(momentumSummary.avg_score) : null;

  useEffect(() => {
    const controller = new AbortController();
    api.getEnabledModules(controller.signal)
      .then(modules => setEnabledModules(modules))
      .catch(() => {
        // On error, show all items (graceful degradation)
      });
    api.getVersion(controller.signal)
      .then(version => setAppVersion(version))
      .catch(() => {
        // On error, leave version hidden
      });
    return () => controller.abort();
  }, []);

  // Close sidebar on navigation (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // Filter nav sections based on enabled modules
  const navSections = useMemo(() => {
    return ALL_NAV_SECTIONS
      .map(section => ({
        ...section,
        items: section.items.filter(item => {
          if (!item.requiresModule) return true;
          // If modules haven't loaded yet, show all (avoid flash of missing items)
          if (enabledModules === null) return true;
          return enabledModules.includes(item.requiresModule);
        }),
      }))
      .filter(section => section.items.length > 0);
  }, [enabledModules]);

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(href);
  };

  const sidebarContent = (
    <>
      {/* Logo/Title */}
      <div className="px-5 pt-6 pb-5 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center shadow-md shadow-primary-500/30">
            <Zap className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">Conduital</h1>
            <p className="text-[11px] text-gray-500 font-medium tracking-wide uppercase">The Conduit for Intelligent Momentum</p>
          </div>
        </div>
        <button
          onClick={() => setSidebarOpen(false)}
          className="md:hidden p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 pb-3 space-y-5 overflow-y-auto">
        {navSections.map((section, sectionIdx) => (
          <div key={sectionIdx}>
            {section.label && (
              <p className="px-3 mb-1.5 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                {section.label}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                const disabled = item.disabled;

                if (disabled) {
                  return (
                    <div
                      key={item.name}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-600 cursor-not-allowed"
                      title="Coming soon"
                    >
                      <Icon className="w-[18px] h-[18px]" />
                      <span className="text-sm">{item.name}</span>
                      <span className="ml-auto text-[10px] bg-gray-800 text-gray-500 px-1.5 py-0.5 rounded font-medium">
                        Soon
                      </span>
                    </div>
                  );
                }

                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      group flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-150
                      ${active
                        ? 'bg-primary-500/15 text-primary-400 font-medium'
                        : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
                      }
                    `}
                    style={active && momentumGlowColor ? {
                      boxShadow: `inset 3px 0 0 ${momentumGlowColor}, 0 0 8px ${momentumGlowColor}20`,
                    } : undefined}
                  >
                    <Icon
                      className={`w-[18px] h-[18px] transition-colors ${
                        active ? 'text-primary-400' : 'text-gray-500 group-hover:text-gray-300'
                      }`}
                    />
                    <span className="text-sm">{item.name}</span>
                    {active && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-400" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User Menu */}
      <div className="px-3 py-3 border-t border-gray-800/60">
        <UserMenu />
      </div>

      {/* Feedback */}
      <div className="px-3 pb-1">
        <FeedbackWidget />
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-800/60">
        <div className="flex items-center justify-center gap-1.5 text-[11px] text-gray-600">
          <CloudCog className="w-3 h-3" />
          <span>File Sync</span>
          {appVersion && (
            <>
              <span className="text-gray-700">·</span>
              <span className="text-gray-700">v{appVersion}</span>
            </>
          )}
        </div>
      </div>
    </>
  );

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile header bar */}
      <div className="fixed top-0 left-0 right-0 z-30 flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800 md:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-primary-500 rounded-md flex items-center justify-center">
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="text-sm font-semibold text-white">Conduital</span>
        </div>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — always visible on md+, slide-in drawer on mobile */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 flex flex-col shadow-xl
          transition-transform duration-200 ease-in-out
          md:static md:translate-x-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {sidebarContent}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto pt-14 md:pt-0">
        <Outlet />
      </main>

      {/* Keyboard Shortcut Overlay */}
      <KeyboardShortcutOverlay />
    </div>
  );
}
