export interface RightPanelVisibility {
  showPanel: boolean;
  showExpandTrigger: boolean;
}

export const getRightPanelVisibility = (
  rightPanelCollapsed: boolean
): RightPanelVisibility => {
  if (rightPanelCollapsed) {
    return {
      showPanel: false,
      showExpandTrigger: true,
    };
  }

  return {
    showPanel: true,
    showExpandTrigger: false,
  };
};
