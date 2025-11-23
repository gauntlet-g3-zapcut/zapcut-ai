import type { ChangeEvent } from "react"

interface SelectOption {
  value: string
  label: string
}

interface SelectFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  helperText?: string
}

export function SelectField({
  id,
  label,
  value,
  onChange,
  options,
  placeholder,
  helperText
}: SelectFieldProps) {
  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onChange(event.target.value)
  }

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="text-sm font-semibold text-foreground">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={handleChange}
        className="w-full rounded-md border border-purple-200 bg-white px-3 py-2 text-sm shadow-sm transition focus:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-300"
      >
        {placeholder ? (
          <option value="" disabled>
            {placeholder}
          </option>
        ) : null}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {helperText ? (
        <p className="text-xs text-muted-foreground leading-relaxed">{helperText}</p>
      ) : null}
    </div>
  )
}

