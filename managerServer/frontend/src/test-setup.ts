import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock @penguintechinc/react-libs for testing
vi.mock('@penguintechinc/react-libs', () => ({
  AppConsoleVersion: vi.fn(() => null),
  LoginPageBuilder: vi.fn(() => null),
  SidebarMenu: vi.fn(() => null),
  FormModalBuilder: vi.fn(() => null),
}))

// Mock api service to avoid actual HTTP calls
vi.mock('./services/api', () => ({
  api: {
    login: vi.fn(),
    logout: vi.fn(),
  },
}))

// Mock localStorage
const store: Record<string, string> = {}
const localStorageMock = {
  getItem: vi.fn((key: string) => store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    store[key] = value.toString()
  }),
  removeItem: vi.fn((key: string) => {
    delete store[key]
  }),
  clear: vi.fn(() => {
    Object.keys(store).forEach(key => delete store[key])
  }),
}
global.localStorage = localStorageMock as any

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
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
