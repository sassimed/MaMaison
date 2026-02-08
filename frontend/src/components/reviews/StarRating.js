import React from 'react';
import { Star } from 'lucide-react';

/**
 * StarRating component - displays star rating (view only or interactive)
 */
export function StarRating({ 
  rating = 0, 
  onRate = null, 
  size = 'md',
  showValue = false,
  totalReviews = null,
  className = ''
}) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8'
  };
  
  const starSize = sizes[size] || sizes.md;
  const isInteractive = typeof onRate === 'function';
  
  const handleClick = (index) => {
    if (isInteractive) {
      onRate(index + 1);
    }
  };
  
  // Render a single star
  const renderStar = (index) => {
    const filled = index < Math.floor(rating);
    const half = !filled && index < rating && rating - index >= 0.5;
    
    return (
      <button
        key={index}
        type="button"
        onClick={() => handleClick(index)}
        disabled={!isInteractive}
        className={
          'relative ' +
          (isInteractive 
            ? 'cursor-pointer hover:scale-110 transition-transform' 
            : 'cursor-default')
        }
      >
        <Star 
          className={starSize + ' text-gray-300'} 
          strokeWidth={1.5}
        />
        
        {(filled || half) && (
          <div 
            className="absolute inset-0 overflow-hidden"
            style={{ width: half ? '50%' : '100%' }}
          >
            <Star 
              className={starSize + ' text-yellow-400 fill-yellow-400'} 
              strokeWidth={1.5}
            />
          </div>
        )}
      </button>
    );
  };
  
  return (
    <div className={'flex items-center gap-1 ' + className}>
      <div className="flex">
        {renderStar(0)}
        {renderStar(1)}
        {renderStar(2)}
        {renderStar(3)}
        {renderStar(4)}
      </div>
      
      {showValue && (
        <span className="ml-1 text-sm font-medium text-gray-700">
          {rating.toFixed(1)}
        </span>
      )}
      
      {totalReviews !== null && (
        <span className="ml-1 text-sm text-gray-500">
          ({totalReviews} avis)
        </span>
      )}
    </div>
  );
}

/**
 * RatingDistribution - shows breakdown of ratings (5 bars)
 */
export function RatingDistribution({ distribution = {}, total = 0 }) {
  const renderBar = (rating) => {
    const count = distribution[rating] || 0;
    const percentage = total > 0 ? (count / total) * 100 : 0;
    
    return (
      <div key={rating} className="flex items-center gap-2">
        <span className="w-3 text-sm text-gray-600">{rating}</span>
        <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-yellow-400 rounded-full transition-all duration-300"
            style={{ width: percentage + '%' }}
          />
        </div>
        <span className="w-8 text-xs text-gray-500 text-right">{count}</span>
      </div>
    );
  };
  
  return (
    <div className="space-y-2">
      {renderBar(5)}
      {renderBar(4)}
      {renderBar(3)}
      {renderBar(2)}
      {renderBar(1)}
    </div>
  );
}

/**
 * ReviewCard - displays a single review
 */
export function ReviewCard({ review, onDelete = null, currentUserId = null }) {
  const canDelete = currentUserId && (review.user_id === currentUserId);
  
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="font-medium text-gray-900">{review.user_name}</p>
          <p className="text-xs text-gray-500">{formatDate(review.created_at)}</p>
        </div>
        <StarRating rating={review.rating} size="sm" />
      </div>
      
      {review.comment && (
        <p className="text-gray-600 text-sm mt-2">{review.comment}</p>
      )}
      
      {canDelete && onDelete && (
        <button
          onClick={() => onDelete(review.id)}
          className="mt-2 text-xs text-red-600 hover:text-red-700"
        >
          Supprimer mon avis
        </button>
      )}
    </div>
  );
}

/**
 * ReviewForm - form to submit a new review
 */
export function ReviewForm({ 
  onSubmit, 
  isLoading = false,
  targetName = '',
  initialRating = 0
}) {
  const [rating, setRating] = React.useState(initialRating);
  const [comment, setComment] = React.useState('');
  const [error, setError] = React.useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (rating === 0) {
      setError('Veuillez sélectionner une note');
      return;
    }
    
    setError('');
    onSubmit({ rating, comment });
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Votre note pour {targetName}
        </label>
        <StarRating 
          rating={rating} 
          onRate={setRating} 
          size="lg"
        />
        {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Votre commentaire (optionnel)
        </label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Partagez votre expérience..."
          rows={4}
          maxLength={1000}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-400 text-right">{comment.length}/1000</p>
      </div>
      
      <button
        type="submit"
        disabled={isLoading || rating === 0}
        className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Envoi...' : 'Publier mon avis'}
      </button>
    </form>
  );
}

/**
 * ReviewSummary - compact summary showing rating + count
 */
export function ReviewSummary({ 
  averageRating = 0, 
  totalReviews = 0, 
  onClick = null,
  size = 'md'
}) {
  const Wrapper = onClick ? 'button' : 'div';
  
  return (
    <Wrapper
      onClick={onClick}
      className={
        'flex items-center gap-1 ' +
        (onClick ? 'hover:opacity-80 cursor-pointer' : '')
      }
    >
      <StarRating rating={averageRating} size={size} />
      <span className="text-sm text-gray-600">
        {averageRating.toFixed(1)} ({totalReviews})
      </span>
    </Wrapper>
  );
}

export default StarRating;
