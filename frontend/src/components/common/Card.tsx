import clsx from 'clsx';
import type { HTMLAttributes, PropsWithChildren } from 'react';

export function Card({ className, children, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={clsx(
        'group/card relative overflow-hidden rounded-[1.6rem] border border-white/20 bg-white/70 p-6 shadow-[0_24px_55px_rgba(14,23,40,0.14)] backdrop-blur-xl transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_32px_70px_rgba(14,23,40,0.18)]',
        className
      )}
      {...props}
    >
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0 bg-white/10"
      />
      <span
        aria-hidden
        className="pointer-events-none absolute -top-24 right-[-6rem] h-52 w-52 rounded-full bg-primary-200/40 blur-3xl transition-all duration-700 group-hover/card:translate-x-6 group-hover/card:translate-y-4 group-hover/card:opacity-80"
      />
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}

export default Card;


