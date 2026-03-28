import { describe, it, expect, vi, beforeEach } from 'vitest'
import { WebSocketService } from './websocket'

// Use vi.hoisted so these variables are available when vi.mock factory runs
const { mockSocket, mockIo } = vi.hoisted(() => {
  const mockSocket = {
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
  }
  const mockIo = vi.fn(() => mockSocket)
  return { mockSocket, mockIo }
})

vi.mock('socket.io-client', () => ({
  io: mockIo,
}))

describe('WebSocketService', () => {
  let service: WebSocketService

  beforeEach(() => {
    vi.clearAllMocks()
    mockIo.mockReturnValue(mockSocket)
    service = new WebSocketService()
  })

  it('creates a new instance with isConnected=false', () => {
    expect(service.getConnectionStatus()).toBe(false)
  })

  it('connect() calls io() and sets up connect handler', async () => {
    // Simulate successful connect event
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') {
        callback()
      }
    })

    await service.connect()
    expect(mockIo).toHaveBeenCalled()
    expect(service.getConnectionStatus()).toBe(true)
  })

  it('connect() rejects on connection error', async () => {
    const error = new Error('Connection refused')
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect_error') {
        callback(error)
      }
    })

    await expect(service.connect()).rejects.toThrow('Connection refused')
    expect(service.getConnectionStatus()).toBe(false)
  })

  it('disconnect() sets isConnected to false', async () => {
    // First connect
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()
    expect(service.getConnectionStatus()).toBe(true)

    service.disconnect()
    expect(service.getConnectionStatus()).toBe(false)
    expect(mockSocket.disconnect).toHaveBeenCalled()
  })

  it('disconnect() does nothing when not connected', () => {
    service.disconnect()
    expect(mockSocket.disconnect).not.toHaveBeenCalled()
  })

  it('onTestStarted() registers test_started event listener', async () => {
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()

    mockSocket.on.mockClear()
    const callback = vi.fn()
    service.onTestStarted(callback)
    expect(mockSocket.on).toHaveBeenCalledWith('test_started', expect.any(Function))
  })

  it('onTestProgress() registers test_progress event listener', async () => {
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()

    mockSocket.on.mockClear()
    const callback = vi.fn()
    service.onTestProgress(callback)
    expect(mockSocket.on).toHaveBeenCalledWith('test_progress', expect.any(Function))
  })

  it('onTestComplete() registers test_complete event listener', async () => {
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()

    mockSocket.on.mockClear()
    const callback = vi.fn()
    service.onTestComplete(callback)
    expect(mockSocket.on).toHaveBeenCalledWith('test_complete', expect.any(Function))
  })

  it('onError() registers error event listener', async () => {
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()

    mockSocket.on.mockClear()
    const callback = vi.fn()
    service.onError(callback)
    expect(mockSocket.on).toHaveBeenCalledWith('error', expect.any(Function))
  })

  it('startTest() emits start_test event when connected', async () => {
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()

    const testData = { test_type: 'http', target: 'example.com' }
    service.startTest(testData)
    expect(mockSocket.emit).toHaveBeenCalledWith('start_test', testData)
  })

  it('startTest() logs error when not connected', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    service.startTest({ test_type: 'http', target: 'example.com' })
    expect(mockSocket.emit).not.toHaveBeenCalled()
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('not connected'))
    consoleSpy.mockRestore()
  })

  it('onTestStarted() does nothing if socket is null (not connected)', () => {
    // Socket is null when service is new and connect() not called
    const callback = vi.fn()
    service.onTestStarted(callback)
    // Should not register on mockSocket since socket is null
    expect(mockSocket.on).not.toHaveBeenCalledWith('test_started', expect.any(Function))
  })

  it('connect() passes auth token from localStorage', async () => {
    localStorage.setItem('access_token', 'my-token')
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
    })
    await service.connect()
    expect(mockIo).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({
      auth: expect.objectContaining({ token: 'my-token' }),
    }))
    localStorage.removeItem('access_token')
  })

  it('connect() sets isConnected=false when disconnect event fires', async () => {
    mockSocket.on.mockImplementation((event: string, callback: Function) => {
      if (event === 'connect') callback()
      if (event === 'disconnect') callback('transport close')
    })
    await service.connect()
    // After connect, isConnected should be true initially but then false from disconnect event
    // The isConnected is set in the connect handler and then overridden by disconnect handler
    expect(service.getConnectionStatus()).toBe(false)
  })
})
