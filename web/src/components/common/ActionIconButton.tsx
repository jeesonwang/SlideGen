import { cn } from '../../utils/classnames';

interface ActionIconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  danger?: boolean;
  variant?: 'toolbar' | 'compact';
}

export const ActionIconButton = ({
  children,
  className,
  danger = false,
  type = 'button',
  variant = 'toolbar',
  ...buttonProps
}: ActionIconButtonProps) => (
  <button
    type={type}
    className={cn(
      'inline-flex shrink-0 items-center justify-center rounded-lg border border-border/60 bg-surface-50 text-text-secondary transition-colors hover:border-brand-border hover:text-brand-strong disabled:cursor-not-allowed disabled:opacity-40',
      variant === 'toolbar' ? 'h-11 w-11 text-[13px]' : 'h-8 w-8 text-[12px]',
      danger && 'hover:text-red-500',
      className
    )}
    {...buttonProps}
  >
    {children}
  </button>
);
