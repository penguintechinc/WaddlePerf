import '@testing-library/jest-dom'
import { vi } from 'vitest'

// jsdom does not implement window.matchMedia — provide a stub
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock @penguintechinc/react-libs for testing
vi.mock('@penguintechinc/react-libs', () => ({
  AppConsoleVersion: vi.fn(() => null),
  LoginPageBuilder: vi.fn(() => null),
  SidebarMenu: vi.fn(() => null),
  FormModalBuilder: vi.fn(() => null),
}))
