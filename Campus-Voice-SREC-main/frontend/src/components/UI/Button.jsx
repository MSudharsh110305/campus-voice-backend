import React from 'react';

export default function Button({
    children,
    variant = "primary",
    className = "",
    isLoading = false,
    ...props
}) {
    const variants = {
        primary:
            "bg-srec-primary hover:bg-srec-primaryHover text-white shadow-md hover:shadow-lg disabled:opacity-70 disabled:cursor-not-allowed",

        secondary:
            "bg-white border border-srec-border text-srec-textPrimary hover:bg-gray-50 disabled:opacity-70 disabled:cursor-not-allowed",

        gold:
            "bg-srec-gold hover:bg-srec-goldLight text-black disabled:opacity-70 disabled:cursor-not-allowed",

        danger:
            "bg-srec-danger hover:bg-red-600 text-white disabled:opacity-70 disabled:cursor-not-allowed",

        ghost:
            "text-srec-primary hover:bg-green-50 disabled:opacity-70 disabled:cursor-not-allowed",
    };

    return (
        <button
            className={`
        px-5 py-2.5
        rounded-xl
        font-medium
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-srec-primary
        flex items-center justify-center gap-2
        ${variants[variant]}
        ${className}
      `}
            disabled={isLoading || props.disabled}
            {...props}
        >
            {isLoading && (
                <svg className="animate-spin h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            )}
            {children}
        </button>
    );
}
