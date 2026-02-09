/**
 * Custom Hooks for Performance Optimization
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

/**
 * Debounce hook - prevents rapid function calls
 */
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Throttle hook - limits function execution rate
 */
export function useThrottle(value, limit = 100) {
  const [throttledValue, setThrottledValue] = useState(value);
  const lastRan = useRef(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, limit - (Date.now() - lastRan.current));

    return () => clearTimeout(handler);
  }, [value, limit]);

  return throttledValue;
}

/**
 * Intersection Observer hook - for lazy loading and infinite scroll
 */
export function useIntersectionObserver(options = {}) {
  const [entry, setEntry] = useState(null);
  const [node, setNode] = useState(null);

  const observer = useRef(null);

  useEffect(() => {
    if (observer.current) observer.current.disconnect();

    observer.current = new IntersectionObserver(
      ([entry]) => setEntry(entry),
      {
        root: options.root || null,
        rootMargin: options.rootMargin || '0px',
        threshold: options.threshold || 0,
      }
    );

    if (node) observer.current.observe(node);

    return () => {
      if (observer.current) observer.current.disconnect();
    };
  }, [node, options.root, options.rootMargin, options.threshold]);

  return [setNode, entry];
}

/**
 * Virtual list hook - renders only visible items
 */
export function useVirtualList({
  items = [],
  itemHeight = 50,
  containerHeight = 500,
  overscan = 5,
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef(null);

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);

  const { virtualItems, totalHeight, startIndex, endIndex } = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.floor((scrollTop + containerHeight) / itemHeight) + overscan
    );

    const virtualItems = items.slice(startIndex, endIndex + 1).map((item, index) => ({
      item,
      index: startIndex + index,
      style: {
        position: 'absolute',
        top: `${(startIndex + index) * itemHeight}px`,
        height: `${itemHeight}px`,
        width: '100%',
      },
    }));

    return {
      virtualItems,
      totalHeight: items.length * itemHeight,
      startIndex,
      endIndex,
    };
  }, [items, itemHeight, containerHeight, scrollTop, overscan]);

  return {
    containerRef,
    containerProps: {
      ref: containerRef,
      onScroll: handleScroll,
      style: {
        height: `${containerHeight}px`,
        overflow: 'auto',
        position: 'relative',
      },
    },
    wrapperProps: {
      style: {
        height: `${totalHeight}px`,
        position: 'relative',
      },
    },
    virtualItems,
    startIndex,
    endIndex,
  };
}

/**
 * Previous value hook - for comparison
 */
export function usePrevious(value) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}

/**
 * Local storage hook with SSR safety
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    if (typeof window === 'undefined') return initialValue;
    
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}

/**
 * Online status hook
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

/**
 * Prefetch hook - preload data on hover
 */
export function usePrefetch(fetchFn) {
  const prefetchedRef = useRef(new Set());

  const prefetch = useCallback((key) => {
    if (prefetchedRef.current.has(key)) return;
    
    prefetchedRef.current.add(key);
    
    // Execute fetch in background
    Promise.resolve(fetchFn(key)).catch(() => {
      // Remove from set on error so it can be retried
      prefetchedRef.current.delete(key);
    });
  }, [fetchFn]);

  return prefetch;
}

/**
 * Idle callback hook - run tasks when browser is idle
 */
export function useIdleCallback(callback, options = {}) {
  useEffect(() => {
    if (typeof window === 'undefined' || !window.requestIdleCallback) {
      // Fallback for Safari
      const timeoutId = setTimeout(callback, 1);
      return () => clearTimeout(timeoutId);
    }

    const idleCallbackId = window.requestIdleCallback(callback, options);
    return () => window.cancelIdleCallback(idleCallbackId);
  }, [callback, options]);
}
