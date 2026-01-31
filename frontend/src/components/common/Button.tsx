import React from 'react';
import { cn } from '../../utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
        return (
            <button
                ref={ref}
                className={cn(
                    'inline-flex items-center justify-center rounded-xl font-bold transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none',
                    {
                        'bg-blue-600 text-white shadow-lg shadow-blue-100 hover:bg-blue-700': variant === 'primary',
                        'bg-blue-50 text-blue-600 hover:bg-blue-100': variant === 'secondary',
                        'hover:bg-gray-100 text-gray-500 hover:text-gray-900': variant === 'ghost',
                        'border border-gray-200 hover:border-blue-400 hover:text-blue-500 bg-white': variant === 'outline',
                        'bg-red-50 text-red-600 hover:bg-red-100': variant === 'danger',
                        'px-3 py-1.5 text-xs': size === 'sm',
                        'px-4 py-2 text-sm': size === 'md',
                        'px-6 py-3 text-base': size === 'lg',
                    },
                    className
                )}
                {...props}
            >
                {children}
            </button>
        );
    }
);
Button.displayName = 'Button';
