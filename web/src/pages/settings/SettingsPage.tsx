/**
 * Settings Page
 */

import { Tabs, Typography } from 'antd';
import {
  SettingOutlined,
  AppstoreOutlined,
  SunOutlined,
  MoonOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import { LLMConfigPage } from '../config/LLMConfigPage';
import { EmbeddingConfigPage } from '../config/EmbeddingConfigPage';
import { useUIStore } from '../../store/uiStore';
import { THEME_MODE_OPTIONS, type ThemeMode } from '../../theme/themeMode';

const { Title, Text } = Typography;

export const SettingsPage = () => {
  const { themeMode, setThemeMode } = useUIStore();

  const getThemeIcon = (mode: ThemeMode) => {
    switch (mode) {
      case 'light':
        return <SunOutlined className="text-lg" />;
      case 'dark':
        return <MoonOutlined className="text-lg" />;
      default:
        return <DesktopOutlined className="text-lg" />;
    }
  };

  const getThemeDescription = (mode: ThemeMode) => {
    switch (mode) {
      case 'light':
        return 'Use a bright interface for daytime work and presentations.';
      case 'dark':
        return 'Reduce glare with darker surfaces and stronger contrast.';
      default:
        return 'Follow your operating system appearance automatically.';
    }
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto w-full max-w-6xl px-6 py-8 space-y-6">
      <section className="rounded-[2rem] border border-border/70 bg-surface-50 p-8 shadow-soft">
        <div className="max-w-3xl space-y-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-border bg-brand-surface px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-brand-strong">
            <SettingOutlined />
            System Settings
          </span>
          <Title level={2} className="!mb-0 !text-text-main">
            Model and System Settings
          </Title>
          <Text className="block text-base leading-7 text-text-secondary">
            Manage language models, embedding models, and default runtime options in one place.
          </Text>
        </div>
      </section>

      <section className="rounded-[2rem] border border-border/70 bg-surface-50 p-6 shadow-soft sm:p-8">
        <div className="max-w-3xl space-y-2">
          <Title level={3} className="!mb-0 !text-text-main">
            Appearance Theme
          </Title>
          <Text className="block text-sm leading-6 text-text-secondary">
            The header offers a quick switch, while this section keeps the full setting. When set to System, the interface follows your operating system light or dark appearance automatically.
          </Text>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-3" role="radiogroup" aria-label="Theme selection">
          {THEME_MODE_OPTIONS.map((option) => {
            const selected = option.value === themeMode;

            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setThemeMode(option.value)}
                role="radio"
                aria-checked={selected}
                className={[
                  'group flex min-h-[124px] w-full flex-col justify-between rounded-2xl border px-4 py-4 text-left transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                  selected
                    ? 'border-brand-border bg-brand-surface text-text-main shadow-soft'
                    : 'border-border/70 bg-surface-50 text-text-secondary hover:border-brand-border hover:bg-surface-100/90 hover:text-text-main',
                ].join(' ')}
              >
                <div className="flex items-start justify-between gap-3">
                  <span
                    className={[
                      'inline-flex h-11 w-11 items-center justify-center rounded-xl border transition-colors',
                      selected
                        ? 'border-brand-border bg-brand-surface text-brand-strong'
                        : 'border-border/70 bg-surface-100/80 text-text-secondary group-hover:border-brand-border group-hover:text-brand-strong',
                    ].join(' ')}
                  >
                    {getThemeIcon(option.value)}
                  </span>
                  <span
                    className={[
                      'inline-flex min-w-[72px] items-center justify-center rounded-full border px-2.5 py-1 text-xs font-semibold transition-colors',
                      selected
                        ? 'border-brand-border bg-brand-surface text-brand-strong'
                        : 'border-border/70 bg-surface-100/80 text-text-muted group-hover:text-text-secondary',
                    ].join(' ')}
                  >
                    {selected ? 'Active' : 'Select'}
                  </span>
                </div>

                <div className="mt-5 space-y-1.5">
                  <div className="text-base font-semibold text-text-main">
                    {option.label}
                  </div>
                  <p className="m-0 text-sm leading-6 text-text-secondary">
                    {getThemeDescription(option.value)}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="rounded-[2rem] border border-border/70 bg-surface-50 p-4 shadow-soft sm:p-6">
        <Tabs
          className="[&_.ant-tabs-nav]:!mb-6 [&_.ant-tabs-tab]:!rounded-xl [&_.ant-tabs-tab]:!px-4 [&_.ant-tabs-tab]:!py-3 [&_.ant-tabs-tab]:!text-sm [&_.ant-tabs-tab]:!font-semibold"
          items={[
            {
              key: 'llm',
              label: (
                <span className="inline-flex items-center gap-2">
                  <SettingOutlined /> LLM
                </span>
              ),
              children: <LLMConfigPage />,
            },
            {
              key: 'embedding',
              label: (
                <span className="inline-flex items-center gap-2">
                  <AppstoreOutlined /> Embeddings
                </span>
              ),
              children: <EmbeddingConfigPage />,
            },
          ]}
        />
      </section>
      </div>
    </div>
  );
};
