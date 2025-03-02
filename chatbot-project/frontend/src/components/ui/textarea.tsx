import React from "react"

const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={`border rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 ${className}`}
        {...props}
      />
    )
  }
)

Textarea.displayName = "Textarea"

export { Textarea }