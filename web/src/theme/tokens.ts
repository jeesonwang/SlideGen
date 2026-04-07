import type { ThemeConfig } from 'antd';
import { theme } from 'antd';
import type { ResolvedTheme } from './themeMode';

const sharedTypography = {
  borderRadius: 10,
  fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif",
  fontSize: 14,
};

const baseComponents: ThemeConfig['components'] = {
  Button: {
    controlHeight: 44,
    controlHeightLG: 48,
    borderRadius: 10,
    borderRadiusLG: 12,
  },
  Card: {
    borderRadiusLG: 16,
  },
  Input: {
    controlHeight: 44,
    controlHeightLG: 48,
    borderRadius: 10,
    borderRadiusLG: 12,
  },
  Select: {
    controlHeight: 44,
    controlHeightLG: 48,
    borderRadius: 10,
    borderRadiusLG: 12,
  },
  Menu: {
    itemBorderRadius: 10,
    itemMarginBlock: 4,
    itemMarginInline: 8,
  },
};

const lightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    ...sharedTypography,
    colorPrimary: '#4380de',
    colorSuccess: '#34aa7f',
    colorWarning: '#9a6700',
    colorError: '#b42318',
    colorInfo: '#4380de',
    colorBgBase: '#f3ede5',
    colorBgContainer: '#fefcf8',
    colorBgElevated: '#fefcf8',
    colorText: '#2e394a',
    colorTextSecondary: '#677484',
    colorBorder: '#d7cfc3',
  },
  components: {
    ...baseComponents,
    Button: {
      ...baseComponents.Button,
      primaryShadow: '0 16px 30px rgba(57, 95, 150, 0.18)',
    },
    Card: {
      ...baseComponents.Card,
      boxShadow: '0 24px 60px rgba(57, 72, 98, 0.12)',
    },
    Select: {
      ...baseComponents.Select,
      optionSelectedBg: 'rgba(67, 128, 222, 0.1)',
    },
  },
};

const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    ...sharedTypography,
    colorPrimary: '#93b8df',
    colorSuccess: '#7bc39d',
    colorWarning: '#f3b557',
    colorError: '#ff8b7d',
    colorInfo: '#93b8df',
    colorBgBase: '#1a1f27',
    colorBgContainer: '#222831',
    colorBgElevated: '#222831',
    colorText: '#edf0f3',
    colorTextSecondary: '#b5bdc6',
    colorBorder: '#535d6a',
  },
  components: {
    ...baseComponents,
    Button: {
      ...baseComponents.Button,
      primaryShadow: '0 10px 22px rgba(147, 184, 223, 0.16)',
    },
    Card: {
      ...baseComponents.Card,
      boxShadow: '0 12px 26px rgba(7, 10, 14, 0.28)',
    },
    Select: {
      ...baseComponents.Select,
      optionSelectedBg: 'rgba(147, 184, 223, 0.18)',
    },
  },
};

export const getAntdThemeConfig = (resolvedTheme: ResolvedTheme): ThemeConfig =>
  resolvedTheme === 'dark' ? darkTheme : lightTheme;
