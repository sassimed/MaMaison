/**
 * API Cache Service for Frontend
 * Caches API responses in memory and localStorage for faster loading
 */

class APICache {
  constructor() {
    this.memoryCache = new Map();
    this.cachePrefix = 'mydar_cache_';
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes in ms
  }

  /**
   * Generate cache key from URL and params
   */
  generateKey(url, params = {}) {
    const paramString = Object.keys(params)
      .sort()
      .map(k => `${k}=${params[k]}`)
      .join('&');
    return `${url}?${paramString}`;
  }

  /**
   * Get from memory cache first, then localStorage
   */
  get(key) {
    // Check memory cache first (fastest)
    if (this.memoryCache.has(key)) {
      const item = this.memoryCache.get(key);
      if (item.expiresAt > Date.now()) {
        return item.data;
      }
      this.memoryCache.delete(key);
    }

    // Check localStorage
    try {
      const stored = localStorage.getItem(this.cachePrefix + key);
      if (stored) {
        const item = JSON.parse(stored);
        if (item.expiresAt > Date.now()) {
          // Also store in memory for faster subsequent access
          this.memoryCache.set(key, item);
          return item.data;
        }
        localStorage.removeItem(this.cachePrefix + key);
      }
    } catch (e) {
      // localStorage not available or quota exceeded
    }

    return null;
  }

  /**
   * Store in both memory and localStorage
   */
  set(key, data, ttl = this.defaultTTL) {
    const item = {
      data,
      expiresAt: Date.now() + ttl,
      cachedAt: Date.now()
    };

    // Always store in memory
    this.memoryCache.set(key, item);

    // Try to store in localStorage
    try {
      localStorage.setItem(this.cachePrefix + key, JSON.stringify(item));
    } catch (e) {
      // localStorage full - clear old entries
      this.clearOldEntries();
      try {
        localStorage.setItem(this.cachePrefix + key, JSON.stringify(item));
      } catch (e2) {
        // Still full, just use memory cache
      }
    }
  }

  /**
   * Delete specific key
   */
  delete(key) {
    this.memoryCache.delete(key);
    try {
      localStorage.removeItem(this.cachePrefix + key);
    } catch (e) {}
  }

  /**
   * Clear all cache entries matching a pattern
   */
  clearPattern(pattern) {
    // Clear memory cache
    for (const key of this.memoryCache.keys()) {
      if (key.includes(pattern)) {
        this.memoryCache.delete(key);
      }
    }

    // Clear localStorage
    try {
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.cachePrefix) && key.includes(pattern)) {
          localStorage.removeItem(key);
        }
      }
    } catch (e) {}
  }

  /**
   * Clear all cache
   */
  clearAll() {
    this.memoryCache.clear();
    try {
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.cachePrefix)) {
          localStorage.removeItem(key);
        }
      }
    } catch (e) {}
  }

  /**
   * Clear old/expired entries from localStorage
   */
  clearOldEntries() {
    try {
      const now = Date.now();
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.cachePrefix)) {
          try {
            const item = JSON.parse(localStorage.getItem(key));
            if (item.expiresAt <= now) {
              localStorage.removeItem(key);
            }
          } catch (e) {
            localStorage.removeItem(key);
          }
        }
      }
    } catch (e) {}
  }

  /**
   * Get cache statistics
   */
  getStats() {
    let memoryCount = 0;
    let memoryValid = 0;
    const now = Date.now();

    for (const [key, item] of this.memoryCache.entries()) {
      memoryCount++;
      if (item.expiresAt > now) memoryValid++;
    }

    let localStorageCount = 0;
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.cachePrefix)) {
          localStorageCount++;
        }
      }
    } catch (e) {}

    return {
      memoryCache: { total: memoryCount, valid: memoryValid },
      localStorage: { total: localStorageCount }
    };
  }
}

// Cache TTL presets (in milliseconds)
export const CacheTTL = {
  VERY_SHORT: 30 * 1000,      // 30 seconds
  SHORT: 60 * 1000,           // 1 minute
  MEDIUM: 5 * 60 * 1000,      // 5 minutes
  LONG: 10 * 60 * 1000,       // 10 minutes
  VERY_LONG: 30 * 60 * 1000,  // 30 minutes
  HOUR: 60 * 60 * 1000,       // 1 hour
};

// Singleton instance
const apiCache = new APICache();

export default apiCache;
