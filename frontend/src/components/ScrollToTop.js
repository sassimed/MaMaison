import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollToTop Component
 * Forces scroll to top on every route change
 * EXCEPT when returning to catalog (to preserve scroll position)
 */
function ScrollToTop() {
  const { pathname } = useLocation();
  const prevPathRef = useRef(pathname);

  useEffect(() => {
    const prevPath = prevPathRef.current;
    prevPathRef.current = pathname;
    
    // Check if we're returning to catalog from a product page
    const isReturningToCatalog = (pathname === '/catalog' || pathname === '/catalogue') && 
                                  prevPath.startsWith('/catalog/') && 
                                  prevPath.length > '/catalog/'.length;
    
    const savedScrollPosition = sessionStorage.getItem('catalogScrollPosition');
    
    if (isReturningToCatalog && savedScrollPosition) {
      // Restore catalog scroll position after content loads
      const scrollPos = parseInt(savedScrollPosition, 10);
      
      // Multiple attempts to restore scroll (content may load progressively)
      const restoreScroll = () => {
        window.scrollTo(0, scrollPos);
        document.documentElement.scrollTop = scrollPos;
        document.body.scrollTop = scrollPos;
      };
      
      // Immediate restore
      restoreScroll();
      
      // Delayed restores for content that loads async
      setTimeout(restoreScroll, 100);
      setTimeout(restoreScroll, 300);
      setTimeout(restoreScroll, 500);
      
      // Don't clear the position here - let CatalogPage handle the product scroll
    } else if (!isReturningToCatalog) {
      // Normal scroll to top for all other pages
      window.scrollTo(0, 0);
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
      
      // For iOS Safari
      if (document.scrollingElement) {
        document.scrollingElement.scrollTop = 0;
      }
    }
  }, [pathname]);

  return null;
}

export default ScrollToTop;
