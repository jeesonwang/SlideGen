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

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto w-full max-w-6xl px-6 py-8 space-y-6">
      <section className="glass-panel rounded-3xl p-8">
        <div className="max-w-3xl space-y-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary-500/20 bg-primary-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-primary-300">
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

      <section className="glass-panel rounded-3xl p-6 sm:p-8">
        <div className="max-w-3xl space-y-2">
          <Title level={4} className="!mb-0 !text-text-main">
            Appearance Theme
          </Title>
          <Text className="block text-sm leading-6 text-text-secondary">
            The header offers a quick switch, while this section keeps the full setting. When set to System, the interface follows your operating system light or dark appearance automatically.
          </Text>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {THEME_MODE_OPTIONS.map((option) => {
            const selected = option.value === themeMode;

            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setThemeMode(option.value)}
                className={[
                  'rounded-2xl border px-4 py-4 text-left transition-all duration-200',
                  selected
                    ? 'border-primary-500/40 bg-primary-500/10 text-text-main shadow-glow/20'
                    : 'border-border/70 bg-surface-50/70 text-text-secondary hover:bg-surface-100 hover:text-text-main',
                ].join(' ')}
              >
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-3 font-semibold">
                    {getThemeIcon(option.value)}
                    {option.label}
                  </span>
                  <span
                    className={[
                      'h-4 w-4 rounded-full border transition-colors',
                      selected
                        ? 'border-primary-400 bg-primary-400'
                        : 'border-border bg-transparent',
                    ].join(' ')}
                  />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="glass-panel rounded-3xl p-4 sm:p-6">
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
