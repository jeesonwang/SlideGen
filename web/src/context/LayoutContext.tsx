/**
 * Layout Context for sharing sidebar state across components
 */

import { createContext, useContext } from 'react';

interface LayoutContextType {
  rightPanelCollapsed: boolean;
  setRightPanelCollapsed: (collapsed: boolean) => void;
}

export const LayoutContext = createContext<LayoutContextType | null>(null);

export const useLayoutContext = () => {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error('useLayoutContext must be used within a LayoutContext.Provider');
  }
  return context;
};
