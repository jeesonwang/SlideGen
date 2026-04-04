export interface RightPanelVisibility {
  showPanel: boolean;
  showExpandTrigger: boolean;
}

export const getRightPanelVisibility = (
  _rightPanelCollapsed: boolean
): RightPanelVisibility => {
  return {
    showPanel: false,
    showExpandTrigger: false,
  };
};
