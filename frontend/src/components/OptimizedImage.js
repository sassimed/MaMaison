/**
 * Optimized Image Component with Lazy Loading
 * - Native lazy loading
 * - Blur-up placeholder effect
 * - Error handling with fallback
 * - Responsive srcset support
 */

import React, { useState, useRef, useEffect, memo } from 'react';

const OptimizedImage = memo(({
  src,
  alt = '',
  className = '',
  width,
  height,
  placeholder = null,
  fallback = '/placeholder-product.png',
  sizes = '100vw',
  priority = false,
  onLoad,
  onError,
  ...props
}) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const imgRef = useRef(null);

  // Check if image is already cached
  useEffect(() => {
    if (imgRef.current?.complete) {
      setLoaded(true);
    }
  }, []);

  const handleLoad = (e) => {
    setLoaded(true);
    onLoad?.(e);
  };

  const handleError = (e) => {
    setError(true);
    onError?.(e);
  };

  // Determine final src
  const finalSrc = error ? fallback : src;

  // Generate srcset for responsive images (if URL supports it)
  const generateSrcSet = (url) => {
    if (!url || url.includes('placeholder') || url.startsWith('data:')) return undefined;
    
    // For Cloudinary-style URLs, we could add width parameters
    // For now, just return the original
    return undefined;
  };

  return (
    <div 
      className={`relative overflow-hidden ${className}`}
      style={{ 
        width: width ? `${width}px` : undefined,
        height: height ? `${height}px` : undefined,
        aspectRatio: width && height ? `${width}/${height}` : undefined
      }}
    >
      {/* Placeholder/Blur backdrop */}
      {!loaded && placeholder && (
        <div 
          className="absolute inset-0 bg-gray-100 animate-pulse"
          style={{ 
            backgroundImage: placeholder ? `url(${placeholder})` : undefined,
            backgroundSize: 'cover',
            filter: 'blur(20px)',
            transform: 'scale(1.1)'
          }}
        />
      )}
      
      {/* Loading skeleton */}
      {!loaded && !placeholder && (
        <div className="absolute inset-0 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 animate-shimmer" />
      )}
      
      {/* Actual image */}
      <img
        ref={imgRef}
        src={finalSrc}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : 'lazy'}
        decoding={priority ? 'sync' : 'async'}
        srcSet={generateSrcSet(src)}
        sizes={sizes}
        onLoad={handleLoad}
        onError={handleError}
        className={`
          w-full h-full object-contain
          transition-opacity duration-300
          ${loaded ? 'opacity-100' : 'opacity-0'}
        `}
        {...props}
      />
    </div>
  );
});

OptimizedImage.displayName = 'OptimizedImage';

export default OptimizedImage;

// Shimmer animation style (add to your CSS)
export const shimmerStyles = `
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.animate-shimmer {
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
`;
