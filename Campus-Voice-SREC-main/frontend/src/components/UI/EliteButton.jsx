
import React from 'react';

/**
 * EliteButton - A premium, reusable button component for the Authority Dashboard
 * Matches the Elite Neumorphic Green-Gold theme (SREC Theme).
 * 
 * Variants:
 * - primary: Green gradient (Default action)
 * - secondary: Gray (Close/Cancel)
 * - success: Green (Resolve/Mark Read)
 * - warning: Yellow/Gold (In Progress/Escalate)
 * - danger: Red (Delete/Spam)
 * - outline: White with Green border (View Details)
 * 
 * Sizes: sm, md, lg
 */
const EliteButton = ({
    children,
    variant = 'primary',
    size = 'md',
    className = '',
    isLoading = false,
    disabled = false,
    ...props
}) => {

    // Base styles
    const baseStyles = "rounded-xl font-medium transition-all duration-200 shadow-[4px_4px_12px_rgba(0,0,0,0.08),-4px_-4px_12px_rgba(255,255,255,0.9)] hover:shadow-[inset_2px_2px_6px_rgba(0,0,0,0.08),inset_-2px_-2px_6px_rgba(255,255,255,0.9)] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-srec-primary focus:ring-offset-2";

    // Size variations
    const sizes = {
        sm: "px-3 py-1.5 text-xs",
        md: "px-5 py-2.5 text-sm",
        lg: "px-6 py-3 text-base",
        icon: "p-2 w-9 h-9 items-center justify-center flex" // Special size for icon buttons
    };

    // Variant styles (Mapped to SREC Theme)
    const variants = {
        primary: "bg-srec-primary text-white hover:bg-srec-primaryHover",
        secondary: "bg-white border border-srec-primary text-srec-primary hover:bg-green-50",
        success: "bg-srec-primaryLight text-white hover:bg-green-600",
        warning: "bg-srec-goldLight text-black hover:bg-srec-gold",
        danger: "bg-srec-danger text-white border border-srec-danger hover:bg-red-700",
        outline: "bg-white border border-srec-primary text-srec-primary hover:bg-srec-background",
        ghost: "bg-transparent shadow-none hover:bg-gray-50 text-gray-500 hover:text-gray-700"
    };

    const finalClassName = `${baseStyles} ${sizes[size] || sizes.md} ${variants[variant] || variants.primary} ${className}`;

    return (
        <button
            className={finalClassName}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading ? (
                <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading...
                </>
            ) : children}
        </button>
    );
};

export default EliteButton;
