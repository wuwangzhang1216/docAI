import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { Input } from '../input'

describe('Input', () => {
  it('renders correctly', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('handles value changes', async () => {
    const handleChange = vi.fn()
    const { user } = render(<Input onChange={handleChange} />)

    const input = screen.getByRole('textbox')
    await user.type(input, 'hello')

    expect(handleChange).toHaveBeenCalled()
  })

  it('shows error state', () => {
    render(<Input id="test" error errorMessage="This field is required" />)

    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('alert')).toHaveTextContent('This field is required')
  })

  it('shows helper text when not in error state', () => {
    render(<Input id="test" helperText="Optional field" />)
    expect(screen.getByText('Optional field')).toBeInTheDocument()
  })

  it('shows error message instead of helper text when in error state', () => {
    render(
      <Input
        id="test"
        error
        errorMessage="Error message"
        helperText="Helper text"
      />
    )
    expect(screen.getByText('Error message')).toBeInTheDocument()
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
  })

  it('renders with left icon', () => {
    render(<Input leftIcon={<span data-testid="left-icon">L</span>} />)
    expect(screen.getByTestId('left-icon')).toBeInTheDocument()
  })

  it('renders with right icon', () => {
    render(<Input rightIcon={<span data-testid="right-icon">R</span>} />)
    expect(screen.getByTestId('right-icon')).toBeInTheDocument()
  })

  it('shows character count when enabled', () => {
    render(<Input showCharCount maxLength={100} value="hello" />)
    expect(screen.getByText('5/100')).toBeInTheDocument()
  })

  it('highlights character count when at max length', () => {
    render(<Input showCharCount maxLength={5} value="hello" />)
    const countElement = screen.getByText('5/5')
    expect(countElement).toHaveClass('text-destructive')
  })

  it('is disabled when disabled prop is true', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('accepts different input types', () => {
    render(<Input type="password" placeholder="Password" />)
    const input = screen.getByPlaceholderText('Password')
    expect(input).toHaveAttribute('type', 'password')
  })

  it('applies custom className', () => {
    render(<Input className="custom-class" />)
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('custom-class')
  })
})
