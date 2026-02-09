import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import analytics from '../services/analytics';

/**
 * Component that tracks page views automatically
 * Place this inside the Router component
 */
const PageTracker = () => {
  const location = useLocation();

  useEffect(() => {
    // Track page view on route change
    const pageTitle = document.title || location.pathname;
    analytics.pageView(pageTitle);
  }, [location.pathname, location.search]);

  return null;
};

export default PageTracker;
