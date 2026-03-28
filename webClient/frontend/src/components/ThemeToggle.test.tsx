import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ThemeToggle from './ThemeToggle'

describe('ThemeToggle component', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('renders the theme toggle button', () => {
    render(<ThemeToggle />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('shows Auto label when no theme is saved', () => {
    render(<ThemeToggle />)
    expect(screen.getByText('Auto')).toBeInTheDocument()
  })

  it('shows Light label when light theme is saved in localStorage', () => {
    localStorage.setItem('theme', 'light')
    render(<ThemeToggle />)
    expect(screen.getByText('Light')).toBeInTheDocument()
  })

  it('shows Dark label when dark theme is saved in localStorage', () => {
    localStorage.setItem('theme', 'dark')
    render(<ThemeToggle />)
    expect(screen.getByText('Dark')).toBeInTheDocument()
  })

  it('cycles from auto -> light when clicked', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(screen.getByText('Light')).toBeInTheDocument()
  })

  it('cycles from light -> dark when clicked twice', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button) // auto -> light
    fireEvent.click(button) // light -> dark
    expect(screen.getByText('Dark')).toBeInTheDocument()
  })

  it('cycles from dark -> auto when clicked three times', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button) // auto -> light
    fireEvent.click(button) // light -> dark
    fireEvent.click(button) // dark -> auto
    expect(screen.getByText('Auto')).toBeInTheDocument()
  })

  it('persists theme selection to localStorage', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button) // auto -> light
    expect(localStorage.getItem('theme')).toBe('light')
  })

  it('sets data-theme attribute on documentElement', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button) // -> light
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('has a title attribute describing the current theme', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('title', 'Theme: Auto')
  })

  it('renders an SVG icon inside the button', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    expect(button.querySelector('svg')).toBeTruthy()
  })
})
