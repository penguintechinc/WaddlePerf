import { render, screen, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { ThemeProvider, useTheme } from './ThemeContext'

function ThemeConsumer() {
  const { theme, setTheme, effectiveTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="effective-theme">{effectiveTheme}</span>
      <button data-testid="set-light" onClick={() => setTheme('light')}>Light</button>
      <button data-testid="set-dark" onClick={() => setTheme('dark')}>Dark</button>
      <button data-testid="set-auto" onClick={() => setTheme('auto')}>Auto</button>
    </div>
  )
}

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    vi.clearAllMocks()
  })

  it('defaults to auto theme with no localStorage', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('auto')
  })

  it('restores stored theme from localStorage', () => {
    localStorage.setItem('theme', 'dark')
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(screen.getByTestId('effective-theme')).toHaveTextContent('dark')
  })

  it('sets effectiveTheme to light when theme is set to light', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    act(() => {
      screen.getByTestId('set-light').click()
    })
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(screen.getByTestId('effective-theme')).toHaveTextContent('light')
  })

  it('sets effectiveTheme to dark when theme is set to dark', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    act(() => {
      screen.getByTestId('set-dark').click()
    })
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
    expect(screen.getByTestId('effective-theme')).toHaveTextContent('dark')
  })

  it('persists theme to localStorage when changed', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    act(() => {
      screen.getByTestId('set-dark').click()
    })
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('sets data-theme attribute on documentElement', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    act(() => {
      screen.getByTestId('set-light').click()
    })
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('switches from dark to light', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    act(() => { screen.getByTestId('set-dark').click() })
    act(() => { screen.getByTestId('set-light').click() })
    expect(screen.getByTestId('effective-theme')).toHaveTextContent('light')
  })

  it('throws when useTheme is called outside ThemeProvider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<ThemeConsumer />)).toThrow('useTheme must be used within a ThemeProvider')
    consoleSpy.mockRestore()
  })

  it('returns to auto theme when set-auto is clicked', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    act(() => { screen.getByTestId('set-dark').click() })
    act(() => { screen.getByTestId('set-auto').click() })
    expect(screen.getByTestId('theme')).toHaveTextContent('auto')
    expect(localStorage.getItem('theme')).toBe('auto')
  })
})
