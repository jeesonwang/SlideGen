export type SectionDropPosition = 'before' | 'after';

interface SectionDropPositionInput {
  sourceIndex: number;
  targetIndex: number;
  pointerY: number;
  targetTop: number;
  targetHeight: number;
}

export const resolveSectionDropPosition = ({
  sourceIndex,
  targetIndex,
  pointerY,
  targetTop,
  targetHeight,
}: SectionDropPositionInput): SectionDropPosition => {
  if (sourceIndex < 0 || targetIndex < 0) {
    return pointerY > targetTop + targetHeight / 2 ? 'after' : 'before';
  }

  if (sourceIndex < targetIndex) {
    return 'after';
  }

  if (sourceIndex > targetIndex) {
    return 'before';
  }

  return pointerY > targetTop + targetHeight / 2 ? 'after' : 'before';
};
