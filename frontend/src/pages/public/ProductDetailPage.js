import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Header from '../../components/layout/Header';
import Footer from '../../components/layout/Footer';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import analytics from '../../services/analytics';
import { ShoppingCart, Heart, ChevronLeft, Download, Play, FileText, Book, Check, Wifi, Cpu, Star, MessageSquare, TrendingUp, Package, Copy, Bot } from 'lucide-react';
import { StarRating, RatingDistribution, ReviewCard, ReviewForm } from '../../components/reviews/StarRating';
import { ProductSEO } from '../../components/SEO';

// Scroll to top helper - aggressive version
const scrollToTop = () => {
  // Multiple methods to ensure scroll works across all browsers
  window.scrollTo(0, 0);
  window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;
  
  // Also scroll any scrollable container
  const main = document.querySelector('main');
  if (main) main.scrollTop = 0;
};

function ProductDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  const containerRef = useRef(null);
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [inCart, setInCart] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [imageList, setImageList] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [reviewStats, setReviewStats] = useState(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [canReview, setCanReview] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewCursor, setReviewCursor] = useState(null);
  const [hasMoreReviews, setHasMoreReviews] = useState(false);
  const [productStats, setProductStats] = useState(null);

  const productId = params.productId;

  // Scroll to top BEFORE paint when component mounts or productId changes
  useLayoutEffect(() => {
    scrollToTop();
  }, [productId, location.key]);

  // Also scroll after first render
  useEffect(() => {
    scrollToTop();
    // And after a small delay to catch any async content
    const timer = setTimeout(scrollToTop, 100);
    return () => clearTimeout(timer);
  }, [productId]);

  // Copy model code to clipboard
  const copyModelCode = (e) => {
    e.preventDefault();
    const code = product?.model_code;
    if (!code) return;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code).catch(() => {
        const textArea = document.createElement('textarea');
        textArea.value = code;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      });
    }
    
    // Visual feedback
    const btn = e.currentTarget;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
    btn.classList.add('bg-green-100');
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.classList.remove('bg-green-100');
    }, 1500);
  };

  // Ask AI about this product
  const askAIAboutProduct = () => {
    // Store product info in sessionStorage for chat widget
    const productInfo = {
      id: product.id,
      name: product.name,
      model_code: product.model_code,
      category: product.category,
      mode: 'question'
    };
    sessionStorage.setItem('chatbot_product_context', JSON.stringify(productInfo));
    
    // Dispatch event to open chat widget with product context
    window.dispatchEvent(new CustomEvent('openChatWithProduct', { detail: productInfo }));
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setProduct(null); // Reset product to show loading state
      try {
        // Fetch product
        const prodRes = await api.get('/products/' + productId);
        const p = prodRes.data;
        setProduct(p);
        
        // Track product view
        analytics.productView(p.id, p.name);
        
        // Build image list
        const imgs = [];
        if (p.image || p.image_url) imgs.push(p.image || p.image_url);
        const galleryImages = p.images || p.gallery_images;
        if (galleryImages && galleryImages.length > 0) {
          for (let idx = 0; idx < galleryImages.length; idx++) {
            const gImg = galleryImages[idx];
            if (gImg) imgs.push(gImg);
          }
        }
        setImageList(imgs);
        
        // Fetch reviews
        try {
          const reviewRes = await api.get('/reviews/product/' + productId);
          setReviews(reviewRes.data.reviews || []);
          setReviewStats(reviewRes.data.stats);
          setReviewCursor(reviewRes.data.pagination?.next_cursor);
          setHasMoreReviews(reviewRes.data.pagination?.has_more || false);
        } catch (e) {
          console.log('Reviews not available');
        }
        
        // Fetch stats
        try {
          const statsRes = await api.get('/reviews/product/' + productId + '/stats');
          setProductStats(statsRes.data);
        } catch (e) {
          console.log('Stats not available');
        }
        
        // Check favorites and cart
        if (auth.user) {
          try {
            const favRes = await api.get('/favorites');
            const cartRes = await api.get('/cart');
            const favList = favRes.data.products || [];
            const cartList = cartRes.data.items || [];
            
            let found = false;
            for (let i = 0; i < favList.length; i++) {
              if (favList[i].id === productId) {
                found = true;
                break;
              }
            }
            setIsFavorite(found);
            
            found = false;
            for (let i = 0; i < cartList.length; i++) {
              if (cartList[i].product_id === productId) {
                found = true;
                break;
              }
            }
            setInCart(found);
            
            // Check can review
            const purchaseRes = await api.get('/my-purchase-requests');
            const purchases = purchaseRes.data || [];
            let canRev = false;
            const validStatuses = ['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE'];
            for (let i = 0; i < purchases.length; i++) {
              const p = purchases[i];
              if (validStatuses.indexOf(p.status) !== -1) {
                const items = p.items || [];
                for (let j = 0; j < items.length; j++) {
                  if (items[j].product_id === productId) {
                    canRev = true;
                    break;
                  }
                }
              }
              if (canRev) break;
            }
            setCanReview(canRev);
          } catch (e) {
            console.error(e);
          }
        }
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
      // Scroll to top after loading completes to ensure we're at the top
      setTimeout(scrollToTop, 50);
    };
    loadData();
  }, [productId, auth.user]);

  const handleAddToCart = async () => {
    if (!auth.user) {
      navigate('/login', { state: { from: '/catalog/' + productId } });
      return;
    }
    setAdding(true);
    try {
      await api.post('/cart', { product_id: productId, quantity: quantity });
      setInCart(true);
    } catch (error) {
      alert('Erreur lors de l\'ajout au panier');
    }
    setAdding(false);
  };

  const handleToggleFavorite = async () => {
    if (!auth.user) {
      navigate('/login', { state: { from: '/catalog/' + productId } });
      return;
    }
    try {
      if (isFavorite) {
        await api.delete('/favorites/' + productId);
        setIsFavorite(false);
      } else {
        await api.post('/favorites', { product_id: productId });
        setIsFavorite(true);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const handleSubmitReview = async (data) => {
    setSubmittingReview(true);
    try {
      await api.post('/reviews', {
        target_type: 'product',
        target_id: productId,
        rating: data.rating,
        comment: data.comment || null
      });
      
      // Refresh reviews
      const reviewRes = await api.get('/reviews/product/' + productId);
      setReviews(reviewRes.data.reviews || []);
      setReviewStats(reviewRes.data.stats);
      
      const statsRes = await api.get('/reviews/product/' + productId + '/stats');
      setProductStats(statsRes.data);
      
      setShowReviewForm(false);
      setHasReviewed(true);
      alert('Merci pour votre avis !');
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi');
    }
    setSubmittingReview(false);
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Supprimer votre avis ?')) return;
    
    try {
      await api.delete('/reviews/' + reviewId);
      const newReviews = [];
      for (let i = 0; i < reviews.length; i++) {
        if (reviews[i].id !== reviewId) {
          newReviews.push(reviews[i]);
        }
      }
      setReviews(newReviews);
      setHasReviewed(false);
      
      const statsRes = await api.get('/reviews/product/' + productId + '/stats');
      setProductStats(statsRes.data);
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  };

  const loadMoreReviews = async () => {
    if (!reviewCursor) return;
    setReviewsLoading(true);
    try {
      const res = await api.get('/reviews/product/' + productId + '?cursor=' + reviewCursor);
      const newReviews = reviews.concat(res.data.reviews || []);
      setReviews(newReviews);
      setReviewCursor(res.data.pagination?.next_cursor);
      setHasMoreReviews(res.data.pagination?.has_more || false);
    } catch (err) {
      console.error(err);
    }
    setReviewsLoading(false);
  };

  const getYoutubeEmbedUrl = (url) => {
    if (!url) return null;
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    if (match) return 'https://www.youtube.com/embed/' + match[1];
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center" style={{ minHeight: 'calc(100vh - 160px)' }}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
            <p className="text-gray-500">Chargement du produit...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 flex items-center justify-center" style={{ minHeight: 'calc(100vh - 160px)' }}>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Produit non trouvé</h1>
            <button onClick={() => navigate('/catalog')} className="text-cyan-600 hover:underline">
              Retour au catalogue
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const embedUrl = getYoutubeEmbedUrl(product.youtube_url);
  const hasCompatibility = product.compatibility && product.compatibility.length > 0;
  const hasDocuments = product.manual_url || product.datasheet_url;
  const currentImage = imageList[selectedImage] || null;

  // Render image thumbnails
  const renderThumbnails = () => {
    if (imageList.length <= 1) return null;
    const thumbs = [];
    for (let i = 0; i < imageList.length; i++) {
      const img = imageList[i];
      const isActive = selectedImage === i && !showVideo;
      thumbs.push(
        <button
          key={'thumb-' + i}
          onClick={() => { setSelectedImage(i); setShowVideo(false); }}
          className={'w-20 h-20 rounded-lg overflow-hidden flex-shrink-0 border-2 transition-all ' + 
            (isActive ? 'border-cyan-500' : 'border-gray-200')}
        >
          <img src={img} alt="" className="w-full h-full object-contain p-1" />
        </button>
      );
    }
    return (
      <div className="flex gap-2 overflow-x-auto pb-2" data-testid="image-thumbnails">
        {thumbs}
      </div>
    );
  };

  // Render compatibility tags
  const renderCompatibility = () => {
    if (!hasCompatibility) return null;
    const tags = [];
    const compList = product.compatibility;
    for (let i = 0; i < compList.length; i++) {
      tags.push(
        <span key={'compat-' + i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
          ✓ {compList[i]}
        </span>
      );
    }
    return (
      <div>
        <h3 className="font-semibold text-gray-900 mb-2">Compatible avec</h3>
        <div className="flex flex-wrap gap-2" data-testid="compatibility-list">
          {tags}
        </div>
      </div>
    );
  };

  // Render reviews list
  const renderReviews = () => {
    if (reviewsLoading && reviews.length === 0) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
        </div>
      );
    }
    
    if (reviews.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <p>Aucun avis client pour ce produit</p>
          {!auth.user && (
            <p className="text-sm mt-2">
              <button onClick={() => navigate('/login')} className="text-cyan-600 hover:underline">
                Connectez-vous
              </button> pour laisser un avis après achat
            </p>
          )}
        </div>
      );
    }
    
    const reviewCards = [];
    for (let i = 0; i < reviews.length; i++) {
      const rev = reviews[i];
      reviewCards.push(
        <ReviewCard
          key={rev.id}
          review={rev}
          onDelete={handleDeleteReview}
          currentUserId={auth.user?.id}
        />
      );
    }
    
    return (
      <div className="space-y-4">
        {reviewCards}
        {hasMoreReviews && (
          <button
            onClick={loadMoreReviews}
            disabled={reviewsLoading}
            className="w-full py-3 text-cyan-600 hover:text-cyan-700 font-medium disabled:opacity-50"
          >
            {reviewsLoading ? 'Chargement...' : 'Voir plus d\'avis'}
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {product && <ProductSEO product={product} />}
      <Header />

      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-3">
          <button 
            onClick={() => {
              const lastCatalogUrl = sessionStorage.getItem('lastCatalogUrl');
              if (lastCatalogUrl) {
                navigate(lastCatalogUrl);
              } else {
                navigate('/catalog');
              }
            }} 
            className="flex items-center text-gray-600 hover:text-cyan-600 transition-colors"
            data-testid="back-to-catalog"
          >
            <ChevronLeft className="w-5 h-5" />
            <span>Retour au catalogue</span>
          </button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 flex-1">
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-6 lg:p-8">
            
            {/* Left column - Images */}
            <div className="space-y-4">
              <div className="relative aspect-square bg-gray-100 rounded-xl overflow-hidden">
                {showVideo && embedUrl ? (
                  <iframe
                    src={embedUrl}
                    title="Product video"
                    className="w-full h-full"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                ) : currentImage ? (
                  <img
                    src={currentImage}
                    alt={product.name}
                    className="w-full h-full object-contain p-4"
                    data-testid="product-main-image"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300">
                    <ShoppingCart className="w-24 h-24" />
                  </div>
                )}
                
                {embedUrl && (
                  <button
                    onClick={() => setShowVideo(!showVideo)}
                    className="absolute bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-red-700 transition-colors"
                    data-testid="video-toggle-btn"
                  >
                    <Play className="w-5 h-5" />
                    {showVideo ? 'Voir images' : 'Voir vidéo'}
                  </button>
                )}
              </div>

              {renderThumbnails()}
            </div>

            {/* Right column - Product info */}
            <div className="space-y-6">
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                  {product.category}
                </span>
              </div>

              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="product-title">{product.name}</h1>
                
                {/* Model code */}
                {product.model_code && (
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-sm text-gray-500">Code modèle:</span>
                    <span className="font-mono font-bold text-purple-600 bg-purple-50 px-2 py-0.5 rounded" data-testid="product-model-code">
                      {product.model_code}
                    </span>
                    <button 
                      onClick={copyModelCode}
                      className="p-1 hover:bg-purple-100 rounded text-purple-500 transition-colors"
                      title="Copier le code"
                      data-testid="copy-model-code-btn"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                )}
                
                {/* Rating and stats */}
                <div className="flex items-center gap-4 mb-3">
                  {reviewStats && reviewStats.total_reviews > 0 ? (
                    <div className="flex items-center gap-2">
                      <StarRating rating={reviewStats.average_rating} size="md" />
                      <span className="text-sm text-gray-600">
                        {reviewStats.average_rating.toFixed(1)} ({reviewStats.total_reviews} avis)
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">Aucun avis</span>
                  )}
                  
                  {productStats && productStats.sales_count > 0 && (
                    <span className="flex items-center gap-1 text-sm text-green-600">
                      <Package className="w-4 h-4" />
                      {productStats.sales_count} vendu{productStats.sales_count > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                
                {product.price ? (
                  <p className="text-3xl font-bold text-cyan-600" data-testid="product-price">{product.price.toFixed(3)} DT</p>
                ) : (
                  <p className="text-xl text-gray-500">Prix sur demande</p>
                )}
              </div>

              <div className="prose prose-gray max-w-none">
                <p className="text-gray-600 leading-relaxed" data-testid="product-description">{product.description}</p>
              </div>

              {product.usage && (
                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-cyan-500" />
                    Usage recommandé
                  </h3>
                  <p className="text-gray-600">{product.usage}</p>
                </div>
              )}

              {renderCompatibility()}

              {hasDocuments && (
                <div className="border-t pt-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Documents à télécharger</h3>
                  <div className="flex flex-wrap gap-3" data-testid="download-links">
                    {product.manual_url && (
                      <a href={product.manual_url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
                        <Book className="w-5 h-5" />
                        Manuel d'utilisation
                        <Download className="w-4 h-4" />
                      </a>
                    )}
                    {product.datasheet_url && (
                      <a href={product.datasheet_url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors">
                        <FileText className="w-5 h-5" />
                        Fiche technique
                        <Download className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Cart section */}
              <div className="border-t pt-6 space-y-4">
                <div className="flex items-center gap-4">
                  <span className="text-gray-700">Quantité :</span>
                  <div className="flex items-center border rounded-lg">
                    <button onClick={() => quantity > 1 && setQuantity(quantity - 1)}
                      className="px-3 py-2 text-gray-600 hover:bg-gray-100" data-testid="quantity-decrease">-</button>
                    <span className="px-4 py-2 font-medium" data-testid="quantity-value">{quantity}</span>
                    <button onClick={() => setQuantity(quantity + 1)}
                      className="px-3 py-2 text-gray-600 hover:bg-gray-100" data-testid="quantity-increase">+</button>
                  </div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleAddToCart}
                    disabled={adding || inCart}
                    className={'flex-1 py-3 px-6 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all ' + 
                      (inCart ? 'bg-green-500 text-white' : 'bg-cyan-500 text-white hover:bg-cyan-600')}
                    data-testid="add-to-cart-btn"
                  >
                    {adding ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : inCart ? (
                      <><Check className="w-5 h-5" /> Dans le panier</>
                    ) : (
                      <><ShoppingCart className="w-5 h-5" /> Ajouter au panier</>
                    )}
                  </button>
                  
                  <button
                    onClick={askAIAboutProduct}
                    className="p-3 rounded-xl border-2 border-purple-300 text-purple-600 hover:bg-purple-50 hover:border-purple-400 transition-all"
                    title="Poser une question à l'IA"
                    data-testid="ask-ai-btn"
                  >
                    <Bot className="w-6 h-6" />
                  </button>
                  
                  <button
                    onClick={handleToggleFavorite}
                    className={'p-3 rounded-xl border-2 transition-all ' + 
                      (isFavorite ? 'bg-red-500 border-red-500 text-white' : 'border-gray-300 text-gray-600 hover:border-red-300 hover:text-red-500')}
                    data-testid="favorite-btn"
                  >
                    <Heart className={'w-6 h-6 ' + (isFavorite ? 'fill-current' : '')} />
                  </button>
                </div>

                {auth.user && inCart && (
                  <button onClick={() => navigate('/dashboard/cart')}
                    className="w-full py-2 text-cyan-600 hover:text-cyan-700 text-center" data-testid="view-cart-link">
                    Voir mon panier →
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Specifications Section */}
        {product.specifications && product.specifications.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden p-6 lg:p-8 mb-8" data-testid="specifications-section">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <FileText className="w-6 h-6 text-cyan-500" />
                Fiche Technique
              </h2>
              <button
                onClick={() => {
                  // Generate and download specs as text file
                  let content = `FICHE TECHNIQUE - ${product.name}\n`;
                  content += `${'='.repeat(50)}\n\n`;
                  product.specifications.forEach(section => {
                    content += `\n${section.name}\n${'-'.repeat(30)}\n`;
                    section.specs.forEach(spec => {
                      content += `${spec.key}: ${spec.value}\n`;
                    });
                  });
                  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `fiche-technique-${product.sku || product.id}.txt`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-cyan-50 text-cyan-700 rounded-lg hover:bg-cyan-100 transition-colors"
                data-testid="download-specs-btn"
              >
                <Download className="w-4 h-4" />
                Télécharger
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {product.specifications.map((section, sectionIdx) => (
                <div 
                  key={sectionIdx} 
                  className={`bg-gray-50 rounded-xl p-4 ${
                    section.specs.length > 8 ? 'md:col-span-2' : ''
                  }`}
                >
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 bg-cyan-500 rounded-full"></span>
                    {section.name}
                  </h3>
                  <div className={`space-y-2 ${section.specs.length > 8 ? 'grid grid-cols-1 md:grid-cols-2 gap-2' : ''}`}>
                    {section.specs.map((spec, specIdx) => (
                      <div 
                        key={specIdx} 
                        className="flex justify-between items-start py-1.5 border-b border-gray-200 last:border-0"
                      >
                        <span className="text-gray-600 text-sm flex-shrink-0 mr-4">{spec.key}</span>
                        <span className="text-gray-900 text-sm font-medium text-right">{spec.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* YouTube Videos Section */}
        {product.videos && product.videos.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden p-6 lg:p-8 mb-8" data-testid="videos-section">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-6">
              <Play className="w-6 h-6 text-red-500" />
              Vidéos du produit
              <span className="text-sm font-normal text-gray-500 ml-2">
                ({product.videos.length} vidéo{product.videos.length > 1 ? 's' : ''})
              </span>
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {product.videos.map((video, idx) => (
                <div 
                  key={idx}
                  className="relative rounded-xl overflow-hidden bg-gray-100 aspect-video group cursor-pointer"
                  onClick={() => {
                    setShowVideo(video.video_id);
                  }}
                  data-testid={`video-thumbnail-${idx}`}
                >
                  <img
                    src={video.thumbnail || `https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
                    alt={`Vidéo ${idx + 1}`}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    onError={(e) => {
                      e.target.src = `https://img.youtube.com/vi/${video.video_id}/hqdefault.jpg`;
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/50 transition-colors">
                    <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <Play className="w-8 h-8 text-white fill-white ml-1" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Video Modal */}
        {showVideo && (
          <div 
            className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4"
            onClick={() => setShowVideo(false)}
          >
            <div className="relative w-full max-w-4xl aspect-video">
              <button
                onClick={() => setShowVideo(false)}
                className="absolute -top-12 right-0 text-white hover:text-gray-300 text-lg"
              >
                ✕ Fermer
              </button>
              <iframe
                src={`https://www.youtube.com/embed/${showVideo}?autoplay=1`}
                className="w-full h-full rounded-xl"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                title="Video produit"
              />
            </div>
          </div>
        )}

        {/* Reviews Section */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden p-6 lg:p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-cyan-500" />
              Avis clients
            </h2>
            
            {auth.user && canReview && !hasReviewed && (
              <button
                onClick={() => setShowReviewForm(true)}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-500 text-white rounded-lg font-medium hover:from-purple-700 hover:to-cyan-600"
                data-testid="write-review-btn"
              >
                Donner mon avis
              </button>
            )}
          </div>

          {/* Review form modal */}
          {showReviewForm && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-xl max-w-md w-full p-6">
                <h3 className="text-xl font-bold mb-4">Votre avis sur {product.name}</h3>
                <ReviewForm
                  onSubmit={handleSubmitReview}
                  isLoading={submittingReview}
                  targetName={product.name}
                />
                <button
                  onClick={() => setShowReviewForm(false)}
                  className="mt-4 w-full py-2 text-gray-600 hover:text-gray-800"
                >
                  Annuler
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Stats column */}
            <div className="lg:col-span-1">
              {reviewStats && reviewStats.total_reviews > 0 ? (
                <div className="bg-gray-50 rounded-xl p-6">
                  <div className="text-center mb-6">
                    <p className="text-5xl font-bold text-gray-900">{reviewStats.average_rating.toFixed(1)}</p>
                    <StarRating rating={reviewStats.average_rating} size="lg" className="justify-center mt-2" />
                    <p className="text-sm text-gray-500 mt-2">{reviewStats.total_reviews} avis</p>
                  </div>
                  
                  <RatingDistribution 
                    distribution={reviewStats.rating_distribution} 
                    total={reviewStats.total_reviews} 
                  />
                  
                  {productStats && productStats.sales_count > 0 && (
                    <div className="mt-6 pt-6 border-t">
                      <div className="flex items-center justify-center gap-2 text-green-600">
                        <TrendingUp className="w-5 h-5" />
                        <span className="font-medium">{productStats.sales_count} ventes</span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-gray-50 rounded-xl p-6 text-center">
                  <Star className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Aucun avis pour le moment</p>
                  {auth.user && canReview && !hasReviewed && (
                    <button
                      onClick={() => setShowReviewForm(true)}
                      className="mt-4 text-cyan-600 hover:text-cyan-700 font-medium"
                    >
                      Soyez le premier à donner votre avis
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Reviews list */}
            <div className="lg:col-span-2">
              {renderReviews()}
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default ProductDetailPage;
