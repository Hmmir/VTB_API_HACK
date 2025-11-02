import clsx from 'clsx';
import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
}

const base = 'group relative inline-flex items-center justify-center overflow-hidden rounded-[1.1rem_1.1rem_0.75rem_0.75rem] font-semibold uppercase tracking-[0.14em] transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-300 focus-visible:ring-offset-white/20 disabled:cursor-not-allowed disabled:opacity-55';

const variants: Record<Variant, string> = {
  primary:
    'bg-gradient-to-br from-primary-300 via-primary-500 to-primary-700 text-white shadow-prism hover:-translate-y-0.5 hover:shadow-[0_22px_55px_rgba(22,122,104,0.33)]',
  secondary:
    'border border-white/50 bg-white/80 text-ink shadow-bevel hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-[0_18px_35px_rgba(18,35,52,0.16)]',
  ghost:
    'text-ink/80 bg-transparent border border-transparent hover:border-primary-200 hover:text-ink hover:bg-white/40',
  danger:
    'bg-gradient-to-r from-roseflare via-roseflare to-roseflare/90 text-white shadow-[0_18px_45px_rgba(255,111,145,0.32)] hover:-translate-y-0.5',
};

const sizes: Record<Size, string> = {
  sm: 'px-4 py-2.5 text-[0.68rem]',
  md: 'px-5 py-3 text-[0.75rem]',
  lg: 'px-6 py-3.5 text-[0.85rem] tracking-[0.18em]'
};

export function Button({
  children,
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  ...props
}: PropsWithChildren<ButtonProps>) {
  return (
    <button
      data-variant={variant}
      data-size={size}
      className={clsx(base, variants[variant], sizes[size], className)}
      {...props}
    >
      <span className="relative z-10 flex items-center gap-2">
        {isLoading ? 'Загрузка…' : children}
      </span>
      <span className="absolute inset-0 z-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" aria-hidden="true">
        <span className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.35),transparent_55%)]" />
      </span>
    </button>
  );
}

export default Button;


