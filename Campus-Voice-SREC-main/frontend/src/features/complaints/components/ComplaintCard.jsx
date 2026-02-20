import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../../../components/UI';
import { useAuth } from '../../../context/AuthContext';
import complaintService from '../../../services/complaint.service';
import { ThumbsUp, ThumbsDown, Sparkles, FileX } from 'lucide-react';
import { Skeleton } from '../../../components/UI';

import { VOTE_TYPES } from '../../../utils/constants';

export default function ComplaintCard({
  id,
  title,
  desc,
  summary,
  rephrased_text,
  category,
  department_code,
  img,
  // img, // Removed img prop
  author,
  status,
  priority,
  upvotes,
  downvotes,
  timestamp,
  isOwner = false,
  has_image = false // Added has_image prop
}) {
  const { user } = useAuth();
  const [voteCount, setVoteCount] = useState({ up: upvotes || 0, down: downvotes || 0 });
  const [userVote, setUserVote] = useState(null);
  const [isVoting, setIsVoting] = useState(false);
  const [imageUrl, setImageUrl] = useState(null); // Added imageUrl state
  const [imageLoading, setImageLoading] = useState(false); // Added imageLoading state

  // Fetch user's existing vote on mount - with delay to prevent rate limiting
  useEffect(() => {
    const fetchMyVote = async () => {
      try {
        const voteData = await complaintService.getMyVote(id);
        setUserVote(voteData.has_voted ? voteData.vote_type : null);
      } catch (error) {
        // Silently fail - user can still vote, we just don't show existing vote
        console.log("Could not fetch vote status:", error.message);
      }
    };

    // Add small random delay to spread out API calls and avoid rate limiting
    const delay = Math.random() * 500;
    const timer = setTimeout(fetchMyVote, delay);
    return () => clearTimeout(timer);
  }, [id]);

  // Fetch image as blob on mount if exists - with delay to prevent rate limiting
  useEffect(() => {
    let active = true;
    if (has_image) {
      setImageLoading(true);

      // Add small random delay to spread out API calls and avoid rate limiting
      const delay = Math.random() * 800;
      const timer = setTimeout(() => {
        complaintService.fetchImage(id, true)
          .then(url => {
            if (active) setImageUrl(url);
          })
          .catch(err => {
            console.log("Could not fetch thumbnail:", err.message);
            if (active) setImageUrl(null); // Set to null on error to show fallback
          })
          .finally(() => {
            if (active) setImageLoading(false);
          });
      }, delay);

      return () => {
        clearTimeout(timer);
        active = false;
        if (imageUrl) {
          URL.revokeObjectURL(imageUrl);
        }
      };
    } else {
      setImageUrl(null); // Ensure no image is shown if has_image is false
    }

    return () => {
      active = false;
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [id, has_image]);

  // Update vote counts when props change
  useEffect(() => {
    setVoteCount({ up: upvotes || 0, down: downvotes || 0 });
  }, [upvotes, downvotes]);

  const handleVote = async (e, type) => {
    e.preventDefault();
    if (!user?.roll_no) {
      alert("Please login to vote");
      return;
    }
    if (isVoting) return;

    setIsVoting(true);

    // Store previous state for rollback
    const prevVote = userVote;
    const prevCount = { ...voteCount };

    // Optimistic UI update
    const isRemoving = userVote === type;
    let newUp = voteCount.up;
    let newDown = voteCount.down;

    if (isRemoving) {
      // Removing vote
      if (type === VOTE_TYPES.UPVOTE) newUp--;
      else newDown--;
      setUserVote(null);
    } else {
      // Adding or changing vote
      if (prevVote === VOTE_TYPES.UPVOTE) newUp--;
      if (prevVote === VOTE_TYPES.DOWNVOTE) newDown--;
      if (type === VOTE_TYPES.UPVOTE) newUp++;
      else newDown++;
      setUserVote(type);
    }

    setVoteCount({ up: Math.max(0, newUp), down: Math.max(0, newDown) });

    try {
      let response;

      // If clicking same vote type, remove vote
      if (isRemoving) {
        response = await complaintService.removeVote(id);
      } else {
        // Add or change vote
        response = await complaintService.voteOnComplaint(id, type);
      }

      // Update with actual backend response
      setVoteCount({
        up: response.upvotes,
        down: response.downvotes
      });
      setUserVote(response.user_vote);

    } catch (error) {
      console.error("Vote failed:", error);

      // Rollback optimistic update
      setVoteCount(prevCount);
      setUserVote(prevVote);

      // Show user-friendly error message
      const errorMsg = error.message?.toLowerCase();
      if (errorMsg?.includes('greenlet') || errorMsg?.includes('sqlalchemy')) {
        alert("Server is temporarily busy. Please try again in a moment.");
      } else if (errorMsg?.includes('rate limit')) {
        alert("Too many requests. Please wait a moment and try again.");
      } else {
        alert("Failed to register vote. Please try again.");
      }
    } finally {
      setIsVoting(false);
    }
  };

  // Display logic based on ownership
  // Public view: Show AI rephrased_text (or fallback to summary/desc)
  // Owner view: Show both description and summary
  const displayContent = isOwner ? null : (rephrased_text || summary || desc);

  return (
    <Link to={`/complaint/${id}`} className="block group">
      <div className="bg-srec-card rounded-xl shadow-neu-flat border border-white/60 overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
        {has_image && (
          <div className="relative h-48 overflow-hidden bg-gray-100">
            {imageLoading ? (
              <Skeleton className="w-full h-full" />
            ) : imageUrl ? (
              <img
                src={imageUrl}
                alt={title}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <FileX size={32} strokeWidth={1.5} />
                <span className="text-xs mt-2">Image failed to load</span>
              </div>
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-60"></div>
          </div>
        )}

        <div className="p-5">
          {/* Badges row - always visible */}
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge type={status} variant="status">{status || 'Pending'}</Badge>
              {priority && (
                <Badge type={priority} variant="priority">{priority}</Badge>
              )}
            </div>
            <span className="text-xs text-gray-400">
              {timestamp ? new Date(timestamp).toLocaleDateString() : ''}
            </span>
          </div>

          {/* Title */}
          <h3 className="font-bold text-lg text-gray-900 mb-2 leading-tight group-hover:text-srec-primary transition-colors">{title}</h3>

          {/* Content display based on ownership */}
          {isOwner ? (
            <>
              {/* Owner view: Show both description and AI summary */}
              {desc && (
                <div className="mb-3">
                  <div className="text-xs text-gray-500 font-medium mb-1">Your submitted description</div>
                  <p className="text-gray-600 text-sm line-clamp-2 leading-relaxed">{desc}</p>
                </div>
              )}
              {summary && (
                <div>
                  <div className="flex items-center gap-1.5 text-xs text-srec-primary font-medium mb-1">
                    <Sparkles size={12} className="text-srec-primary" />
                    <span>Reviewed Summary</span>
                  </div>
                  <p className="text-gray-600 text-sm line-clamp-2 leading-relaxed">{summary}</p>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Public view: Only show AI summary */}
              {summary && (
                <div className="flex items-center gap-1.5 text-xs text-srec-primary font-medium mb-1.5">
                  <Sparkles size={12} className="text-srec-primary" />
                  <span>Reviewed Summary</span>
                </div>
              )}
              <p className="text-gray-600 text-sm mb-4 line-clamp-3 leading-relaxed">{displayContent}</p>
            </>
          )}

          {/* Category Badge + Metadata */}
          <div className="flex flex-wrap items-center gap-2 mb-4">
            {category && (
              <Badge type={category} variant="category">{category}</Badge>
            )}
            {department_code && (
              <Badge variant="category" className="bg-blue-50 text-blue-700 border-blue-200">
                {department_code}
              </Badge>
            )}
            {img && timestamp && (
              <span className="text-xs text-gray-400 ml-auto">
                {new Date(timestamp).toLocaleDateString()}
              </span>
            )}
          </div>

          {/* Voting Section with helper text */}
          <div className="pt-4 border-t border-gray-100">
            <div className="flex items-center gap-3">
              {/* Upvote Button */}
              <button
                onClick={(e) => handleVote(e, VOTE_TYPES.UPVOTE)}
                disabled={isVoting}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
                  transition-all duration-200
                  ${userVote === VOTE_TYPES.UPVOTE
                    ? 'bg-emerald-100 text-emerald-700 shadow-inner border border-emerald-200'
                    : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-600 hover:shadow-vote-glow'
                  }
                  active:scale-95
                `}
                title="Upvote"
              >
                <ThumbsUp size={16} className={userVote === VOTE_TYPES.UPVOTE ? 'fill-current' : ''} />
                <span>{voteCount.up}</span>
              </button>

              {/* Downvote Button */}
              <button
                onClick={(e) => handleVote(e, VOTE_TYPES.DOWNVOTE)}
                disabled={isVoting}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
                  transition-all duration-200
                  ${userVote === VOTE_TYPES.DOWNVOTE
                    ? 'bg-srec-danger/10 text-srec-danger shadow-inner border border-srec-danger/20'
                    : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-srec-danger/5 hover:border-srec-danger/30 hover:text-srec-danger hover:shadow-vote-glow-down'
                  }
                  active:scale-95
                `}
                title="Downvote"
              >
                <ThumbsDown size={16} className={userVote === VOTE_TYPES.DOWNVOTE ? 'fill-current' : ''} />
                <span>{voteCount.down}</span>
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-3 font-medium">
              👆 Helps authorities prioritise this issue
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
