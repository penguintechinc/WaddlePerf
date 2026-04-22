import { describe, it, expect } from 'vitest'
import {
  validateTarget,
  validateDNSQuery,
  validatePort,
  validateTimeout,
  validateCount,
  validateHTTPProtocol,
  validateTCPProtocol,
  validateUDPProtocol,
  validateICMPProtocol,
  sanitizeString,
  MAX_TARGET_LENGTH,
  MAX_TIMEOUT_SECONDS,
  MAX_COUNT,
  MIN_PORT,
  MAX_PORT,
} from './validation'

describe('validateTarget', () => {
  it('rejects empty target', () => {
    expect(validateTarget('')).toEqual({ valid: false, error: 'Target cannot be empty' })
    expect(validateTarget('   ')).toEqual({ valid: false, error: 'Target cannot be empty' })
  })

  it('rejects target exceeding max length', () => {
    const longTarget = 'a'.repeat(MAX_TARGET_LENGTH + 1)
    const result = validateTarget(longTarget)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('maximum length')
  })

  it('accepts valid IP addresses', () => {
    expect(validateTarget('8.8.8.8')).toEqual({ valid: true })
    expect(validateTarget('192.168.1.1')).toEqual({ valid: true })
    expect(validateTarget('255.255.255.255')).toEqual({ valid: true })
    expect(validateTarget('0.0.0.0')).toEqual({ valid: true })
  })

  it('accepts valid hostnames', () => {
    expect(validateTarget('example.com')).toEqual({ valid: true })
    expect(validateTarget('www.google.com')).toEqual({ valid: true })
    expect(validateTarget('subdomain.example.org')).toEqual({ valid: true })
    expect(validateTarget('localhost')).toEqual({ valid: true })
  })

  it('accepts valid URLs and strips scheme', () => {
    expect(validateTarget('https://example.com')).toEqual({ valid: true })
    expect(validateTarget('http://example.com')).toEqual({ valid: true })
  })

  it('rejects invalid URL format', () => {
    const result = validateTarget('not://valid url with spaces')
    expect(result.valid).toBe(false)
  })

  it('accepts target with port (strips port)', () => {
    expect(validateTarget('example.com:443')).toEqual({ valid: true })
  })

  it('rejects invalid hostname format', () => {
    const result = validateTarget('invalid_hostname!')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Invalid hostname format')
  })
})

describe('validateDNSQuery', () => {
  it('rejects empty query', () => {
    expect(validateDNSQuery('')).toEqual({ valid: false, error: 'DNS query cannot be empty' })
    expect(validateDNSQuery('   ')).toEqual({ valid: false, error: 'DNS query cannot be empty' })
  })

  it('rejects query exceeding max length', () => {
    const longQuery = 'a.'.repeat(130)
    const result = validateDNSQuery(longQuery)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('maximum length')
  })

  it('accepts valid domain names', () => {
    expect(validateDNSQuery('google.com')).toEqual({ valid: true })
    expect(validateDNSQuery('example.org')).toEqual({ valid: true })
    expect(validateDNSQuery('sub.domain.com')).toEqual({ valid: true })
  })

  it('rejects invalid domain formats', () => {
    const result = validateDNSQuery('invalid domain!')
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Invalid domain name format')
  })
})

describe('validatePort', () => {
  it('accepts valid port numbers', () => {
    expect(validatePort(80)).toEqual({ valid: true })
    expect(validatePort(443)).toEqual({ valid: true })
    expect(validatePort(MIN_PORT)).toEqual({ valid: true })
    expect(validatePort(MAX_PORT)).toEqual({ valid: true })
    expect(validatePort('8080')).toEqual({ valid: true })
  })

  it('rejects port below minimum', () => {
    expect(validatePort(0)).toEqual({ valid: false, error: `Port must be between ${MIN_PORT} and ${MAX_PORT}` })
    expect(validatePort(-1)).toEqual({ valid: false, error: `Port must be between ${MIN_PORT} and ${MAX_PORT}` })
  })

  it('rejects port above maximum', () => {
    expect(validatePort(MAX_PORT + 1)).toEqual({ valid: false, error: `Port must be between ${MIN_PORT} and ${MAX_PORT}` })
    expect(validatePort(99999)).toEqual({ valid: false, error: `Port must be between ${MIN_PORT} and ${MAX_PORT}` })
  })

  it('rejects non-numeric port string', () => {
    expect(validatePort('abc')).toEqual({ valid: false, error: 'Port must be a number' })
    expect(validatePort(NaN)).toEqual({ valid: false, error: 'Port must be a number' })
  })
})

describe('validateTimeout', () => {
  it('accepts valid timeout values', () => {
    expect(validateTimeout(1)).toEqual({ valid: true })
    expect(validateTimeout(30)).toEqual({ valid: true })
    expect(validateTimeout(MAX_TIMEOUT_SECONDS)).toEqual({ valid: true })
    expect(validateTimeout('30')).toEqual({ valid: true })
  })

  it('rejects timeout below minimum', () => {
    expect(validateTimeout(0)).toEqual({ valid: false, error: 'Timeout must be at least 1 second' })
    expect(validateTimeout(-5)).toEqual({ valid: false, error: 'Timeout must be at least 1 second' })
  })

  it('rejects timeout exceeding maximum', () => {
    const result = validateTimeout(MAX_TIMEOUT_SECONDS + 1)
    expect(result.valid).toBe(false)
    expect(result.error).toContain(`${MAX_TIMEOUT_SECONDS}`)
  })

  it('rejects non-numeric timeout', () => {
    expect(validateTimeout('abc')).toEqual({ valid: false, error: 'Timeout must be a number' })
  })
})

describe('validateCount', () => {
  it('accepts valid count values', () => {
    expect(validateCount(1)).toEqual({ valid: true })
    expect(validateCount(10)).toEqual({ valid: true })
    expect(validateCount(MAX_COUNT)).toEqual({ valid: true })
    expect(validateCount('5')).toEqual({ valid: true })
  })

  it('rejects count below minimum', () => {
    expect(validateCount(0)).toEqual({ valid: false, error: 'Count must be at least 1' })
    expect(validateCount(-1)).toEqual({ valid: false, error: 'Count must be at least 1' })
  })

  it('rejects count exceeding maximum', () => {
    const result = validateCount(MAX_COUNT + 1)
    expect(result.valid).toBe(false)
    expect(result.error).toContain(`${MAX_COUNT}`)
  })

  it('rejects non-numeric count', () => {
    expect(validateCount('abc')).toEqual({ valid: false, error: 'Count must be a number' })
  })
})

describe('validateHTTPProtocol', () => {
  it('accepts empty protocol (uses default)', () => {
    expect(validateHTTPProtocol('')).toEqual({ valid: true })
    expect(validateHTTPProtocol('   ')).toEqual({ valid: true })
  })

  it('accepts valid HTTP protocols', () => {
    expect(validateHTTPProtocol('http1')).toEqual({ valid: true })
    expect(validateHTTPProtocol('http2')).toEqual({ valid: true })
    expect(validateHTTPProtocol('http3')).toEqual({ valid: true })
    expect(validateHTTPProtocol('HTTP/1.1')).toEqual({ valid: true })
    expect(validateHTTPProtocol('HTTP/2')).toEqual({ valid: true })
    expect(validateHTTPProtocol('HTTP/3')).toEqual({ valid: true })
    expect(validateHTTPProtocol('http/2')).toEqual({ valid: true })
  })

  it('rejects invalid HTTP protocol', () => {
    const result = validateHTTPProtocol('ftp')
    expect(result.valid).toBe(false)
    expect(result.error).toBe('Invalid HTTP protocol')
  })
})

describe('validateTCPProtocol', () => {
  it('accepts empty protocol (uses default)', () => {
    expect(validateTCPProtocol('')).toEqual({ valid: true })
  })

  it('accepts valid TCP protocols', () => {
    expect(validateTCPProtocol('raw')).toEqual({ valid: true })
    expect(validateTCPProtocol('tls')).toEqual({ valid: true })
    expect(validateTCPProtocol('TLS')).toEqual({ valid: true })
    expect(validateTCPProtocol('ssh')).toEqual({ valid: true })
    expect(validateTCPProtocol('SSH')).toEqual({ valid: true })
    expect(validateTCPProtocol('Raw TCP')).toEqual({ valid: true })
  })

  it('rejects invalid TCP protocol', () => {
    const result = validateTCPProtocol('ftp')
    expect(result.valid).toBe(false)
    expect(result.error).toBe('Invalid TCP protocol')
  })
})

describe('validateUDPProtocol', () => {
  it('accepts empty protocol (uses default)', () => {
    expect(validateUDPProtocol('')).toEqual({ valid: true })
  })

  it('accepts valid UDP protocols', () => {
    expect(validateUDPProtocol('dns')).toEqual({ valid: true })
    expect(validateUDPProtocol('DNS')).toEqual({ valid: true })
    expect(validateUDPProtocol('raw')).toEqual({ valid: true })
    expect(validateUDPProtocol('udp')).toEqual({ valid: true })
  })

  it('rejects invalid UDP protocol', () => {
    const result = validateUDPProtocol('tcp')
    expect(result.valid).toBe(false)
    expect(result.error).toBe('Invalid UDP protocol')
  })
})

describe('validateICMPProtocol', () => {
  it('accepts empty protocol (uses default)', () => {
    expect(validateICMPProtocol('')).toEqual({ valid: true })
  })

  it('accepts valid ICMP protocols', () => {
    expect(validateICMPProtocol('ping')).toEqual({ valid: true })
    expect(validateICMPProtocol('traceroute')).toEqual({ valid: true })
  })

  it('rejects invalid ICMP protocol', () => {
    const result = validateICMPProtocol('udp')
    expect(result.valid).toBe(false)
    expect(result.error).toBe('Invalid ICMP protocol')
  })
})

describe('sanitizeString', () => {
  it('trims leading and trailing whitespace', () => {
    expect(sanitizeString('  hello  ', 100)).toBe('hello')
  })

  it('truncates to maxLength', () => {
    const result = sanitizeString('abcde', 3)
    expect(result).toBe('abc')
    expect(result.length).toBe(3)
  })

  it('removes control characters', () => {
    const withControl = 'hello\x00world\x01!'
    const result = sanitizeString(withControl, 100)
    expect(result).toBe('helloworld!')
  })

  it('preserves tab, newline, and carriage return', () => {
    const withAllowed = 'hello\tworld\nfoo\rbar'
    const result = sanitizeString(withAllowed, 100)
    expect(result).toContain('\t')
    expect(result).toContain('\n')
    expect(result).toContain('\r')
  })

  it('handles empty string', () => {
    expect(sanitizeString('', 100)).toBe('')
  })

  it('handles string at exact max length', () => {
    const exact = 'a'.repeat(10)
    expect(sanitizeString(exact, 10)).toBe(exact)
  })
})
