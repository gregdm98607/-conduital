import { useState, useEffect, useMemo } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { api } from '@/services/api';
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
} from 'lucide-react';
import { UserMenu } from '@/components/auth/UserMenu';

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
      { name: 'Inbox', href: '/inbox', icon: Inbox, requiresModule: 'gtd_inbox' },
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

  useEffect(() => {
    const controller = new AbortController();
    api.getEnabledModules(controller.signal)
      .then(modules => setEnabledModules(modules))
      .catch(() => {
        // On error, show all items (graceful degradation)
      });
    return () => controller.abort();
  }, []);

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

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 flex flex-col shadow-xl">
        {/* Logo/Title */}
        <div className="px-5 pt-6 pb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center shadow-md shadow-primary-500/30">
              <Zap className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">Project Tracker</h1>
              <p className="text-[11px] text-gray-500 font-medium tracking-wide uppercase">GTD + Momentum</p>
            </div>
          </div>
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
                          ? 'bg-primary-500/15 text-primary-400 font-medium shadow-sm shadow-primary-500/5'
                          : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
                        }
                      `}
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

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-800/60">
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-gray-600">
            <CloudCog className="w-3 h-3" />
            <span>Second Brain Sync</span>
            <span className="text-gray-700">·</span>
            <span className="text-gray-700">v1.0</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
