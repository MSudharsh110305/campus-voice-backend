import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TopNav } from '../../../components/Navbars';
import BottomNav from '../../../components/BottomNav';
import { Card, Button } from '../../../components/UI';
import ComplaintCard from '../components/ComplaintCard';
import { useAuth } from '../../../context/AuthContext';
import complaintService from '../../../services/complaint.service';
import studentService from '../../../services/student.service';
import { Upload, X, Lock, FileX } from 'lucide-react';
import { VISIBILITY } from '../../../utils/constants';

export default function Posts() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('create');
  const [formData, setFormData] = useState({
    original_text: '',
    image: null,
    visibility: 'Public',
  });
  const [imagePreview, setImagePreview] = useState(null);
  const [myPosts, setMyPosts] = useState([]);
  const [submitted, setSubmitted] = useState(false);
  const [apiResponse, setApiResponse] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Image must be less than 5MB');
        return;
      }
      // Validate type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        alert('Only JPEG, PNG, GIF, and WebP images are allowed');
        return;
      }
      setFormData({ ...formData, image: file });
      setImagePreview(URL.createObjectURL(file));
    }
  };



  useEffect(() => {
    const fetchMyComplaints = async () => {
      if (activeTab === 'mine') {
        try {
          const response = await studentService.getMyComplaints({ skip: 0, limit: 50 });
          console.log('📋 My Complaints Response:', response);
          if (Array.isArray(response)) {
            setMyPosts(response);
          } else if (response && Array.isArray(response.complaints)) {
            setMyPosts(response.complaints);
          } else if (response && Array.isArray(response.data)) {
            setMyPosts(response.data);
          } else {
            setMyPosts([]);
          }
        } catch (error) {
          console.error("Failed to fetch complaints:", error);
          setMyPosts([]);
        }
      }
    };

    fetchMyComplaints();
  }, [activeTab]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate original_text
    if (!formData.original_text || formData.original_text.trim().length < 10) {
      alert('Complaint text must be at least 10 characters.');
      return;
    }

    if (formData.original_text.length > 2000) {
      alert('Complaint text must not exceed 2000 characters.');
      return;
    }

    // Check for ALL CAPS
    const textWithoutSpaces = formData.original_text.replace(/\s/g, '');
    if (textWithoutSpaces === textWithoutSpaces.toUpperCase() && /[A-Z]/.test(textWithoutSpaces)) {
      alert('Please avoid writing in ALL CAPS.');
      return;
    }

    setIsSubmitting(true);

    try {
      // Build FormData
      const fd = new FormData();
      fd.append('original_text', formData.original_text);
      fd.append('visibility', formData.visibility); // "Private" or "Public"
      if (formData.image) {
        fd.append('image', formData.image);
      }

      const response = await complaintService.submitComplaint(fd);

      // Upload image separately if exists
      if (formData.image) {
        try {
          await complaintService.uploadImage(response.id, formData.image);
        } catch (uploadError) {
          console.error("Image upload failed:", uploadError);
          // We don't fail the whole submission, but alert the user
          alert("Complaint submitted, but image upload failed. You can try verifying it later in details.");
        }
      }

      setApiResponse(response);
      setSubmitted(true);


      // Optimistically update list
      const newPost = {
        id: response.id || Date.now(),
        submitted_at: new Date().toISOString(),
        status: response.status || 'Pending',
        category: response.category,
        priority: response.priority,
        upvotes: 0,
        ...response
      };
      setMyPosts([newPost, ...myPosts]);

      // Reset form
      setFormData({
        original_text: '',
        image: null,
        visibility: 'Public',
      });
      setImagePreview(null);

    } catch (error) {
      console.error(error);
      alert(error.message || 'Failed to submit complaint');
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClass = "w-full rounded-lg border border-srec-border bg-gray-50/50 px-4 py-2.5 text-sm text-srec-textPrimary shadow-sm placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-srec-primary/50 transition-all";


  // Success screen
  if (submitted && apiResponse) {
    return (
      <div className="fixed inset-0 z-50 min-h-screen bg-srec-background/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="max-w-lg w-full mx-auto p-8 bg-white rounded-2xl shadow-xl overflow-y-auto max-h-[90vh] border border-white/60">
          <div className="mb-6 flex justify-center">
            <div className="w-20 h-20 bg-srec-primary/10 rounded-full flex items-center justify-center shadow-inner">
              <svg className="w-10 h-10 text-srec-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Complaint Submitted!</h2>
            <p className="text-gray-500">AI has analyzed your complaint.</p>
          </div>

          <div className="space-y-4 bg-gray-50 p-6 rounded-xl border border-gray-100 mb-8">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Status</span>
                <p className="font-semibold text-gray-900">{apiResponse.status || 'Pending'}</p>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Category</span>
                <p className="font-medium text-srec-primary">{apiResponse.category || 'AI Analysis Pending'}</p>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Priority</span>
                <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold mt-1
                     ${apiResponse.priority === 'High' ? 'bg-red-50 text-error' : 'bg-green-50 text-srec-primary'}`}>
                  {apiResponse.priority || 'Normal'}
                </span>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Assigned To</span>
                <p className="font-medium text-gray-900">{apiResponse.assigned_authority || 'Pending'}</p>
              </div>
              {apiResponse.target_department_code && (
                <div>
                  <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Department</span>
                  <p className="font-medium text-gray-900">{apiResponse.target_department_code}</p>
                </div>
              )}
              {apiResponse.cross_department && (
                <div>
                  <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Routing</span>
                  <p className="font-medium text-orange-600">Cross-Department</p>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-gray-200">
              <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">AI Rephrased Complaint</span>
              <p className="text-sm text-gray-700 mt-1 italic leading-relaxed">"{apiResponse.rephrased_text || apiResponse.summary || 'Processing...'}"</p>
            </div>

            {apiResponse.has_image && apiResponse.image_verification_status && (
              <div className="pt-4 border-t border-gray-200">
                <span className="text-xs text-gray-400 uppercase tracking-wide font-bold">Image Verification</span>
                <p className={`text-sm mt-1 ${apiResponse.image_verified ? 'text-green-600' : 'text-orange-600'}`}>
                  {apiResponse.image_verification_message || apiResponse.image_verification_status}
                </p>
              </div>
            )}

            {apiResponse.llm_failed && (
              <div className="pt-4 border-t border-gray-200 bg-yellow-50 -mx-6 -mb-6 px-6 py-4 rounded-b-xl">
                <p className="text-xs text-yellow-700">
                  ⚠️ AI analysis is temporarily unavailable. Your complaint has been submitted and will be manually reviewed.
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="secondary"
              onClick={() => {
                setSubmitted(false);
                setApiResponse(null);
                setActiveTab('mine');
              }}
              className="py-3"
            >
              View My Posts
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setSubmitted(false);
                setApiResponse(null);
                navigate('/home');
              }}
              className="py-3"
            >
              Go to Home
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-srec-background">
      <TopNav />

      <div className="max-w-3xl mx-auto p-4 sm:p-6 pb-24 md:pl-24 transition-all duration-300">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Posts</h1>

          <div className="flex bg-white rounded-lg shadow-sm border border-srec-border p-1">
            <button
              onClick={() => setActiveTab('create')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'create'
                ? 'bg-srec-primary text-white shadow-md'
                : 'text-gray-500 hover:text-gray-900'
                }`}
            >
              Create
            </button>
            <button
              onClick={() => setActiveTab('mine')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'mine'
                ? 'bg-srec-primary text-white shadow-md'
                : 'text-gray-500 hover:text-gray-900'
                }`}
            >
              My Posts
            </button>
          </div>
        </div>

        {activeTab === 'create' && (
          <Card className="p-6 sm:p-8 shadow-sm">
            {/* Privacy Reassurance Banner */}
            <div className="flex items-center gap-3 p-4 mb-6 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-100 shadow-sm">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center shadow-inner text-amber-600">
                <Lock size={18} />
              </div>
              <div>
                <h4 className="text-sm font-bold text-amber-800">Anonymous Posting</h4>
                <p className="text-xs text-amber-700/80 font-medium mt-0.5">
                  Your identity is hidden from other students. Only authorities can see your details.
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Describe your complaint</label>
                <textarea
                  name="original_text"
                  value={formData.original_text}
                  onChange={handleChange}
                  placeholder="Tell us what happened in detail (10-2000 characters)..."
                  rows={6}
                  minLength={10}
                  maxLength={2000}
                  className={inputClass}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.original_text.length} / 2000 characters
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Complaint Visibility</label>
                <div className="flex gap-4">
                  <label className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-all duration-200 ${formData.visibility === 'Public' ? 'border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm ring-1 ring-emerald-500/20' : 'border-gray-200 bg-white hover:bg-gray-50 text-gray-600'}`}>
                    <input
                      type="radio"
                      name="visibility"
                      value="Public"
                      checked={formData.visibility === 'Public'}
                      onChange={handleChange}
                      className="hidden"
                    />
                    <span className="font-bold">Public</span>
                  </label>
                  <label className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-all duration-200 ${formData.visibility === 'Private' ? 'border-amber-500 bg-amber-50 text-amber-700 shadow-sm ring-1 ring-amber-500/20' : 'border-gray-200 bg-white hover:bg-gray-50 text-gray-600'}`}>
                    <input
                      type="radio"
                      name="visibility"
                      value="Private"
                      checked={formData.visibility === 'Private'}
                      onChange={handleChange}
                      className="hidden"
                    />
                    <span className="font-bold">Private</span>
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  {formData.visibility === 'Public'
                    ? "Visible to all students in the public feed."
                    : "Visible only to you and the assigned authority."}
                </p>
              </div>



              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Add a photo (optional)
                  <span className="text-gray-400 font-normal ml-1">(helps us understand better)</span>
                </label>

                {!imagePreview ? (
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors border-gray-300 bg-gray-50 hover:bg-gray-100">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 mb-2 text-gray-400" />
                      <p className="text-xs text-gray-500 font-medium">Click to upload image (max 5MB)</p>
                      <p className="text-xs text-gray-400 mt-1">JPEG, PNG, GIF, or WebP</p>
                    </div>
                    <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
                  </label>
                ) : (
                  <div className="relative rounded-xl overflow-hidden border border-gray-200">
                    <img src={imagePreview} alt="Preview" className="w-full h-48 object-cover" />
                    <button
                      type="button"
                      onClick={() => {
                        setFormData({ ...formData, image: null });
                        setImagePreview(null);
                      }}
                      className="absolute top-2 right-2 p-1.5 bg-black/50 text-white rounded-full hover:bg-black/70 transition-colors backdrop-blur-sm"
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}
              </div>

              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
                className="w-full py-3 mt-4"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Grievance'}
              </Button>
            </form>
          </Card>
        )}

        {/* --- My Posts --- */}
        {activeTab === 'mine' && (
          <div className="space-y-5">
            {(!Array.isArray(myPosts) || myPosts.length === 0) ? (
              <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-100">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-50 flex items-center justify-center">
                  <FileX size={28} className="text-gray-400" />
                </div>
                <p className="text-gray-600 text-lg font-medium">You haven't raised any issues yet</p>
                <p className="text-gray-400 text-sm mt-2 max-w-xs mx-auto">
                  Your submitted issues will appear here so you can track their progress.
                </p>
                <Button variant="ghost" className="mt-4 text-srec-primary font-semibold" onClick={() => setActiveTab('create')}>
                  Raise your first issue →
                </Button>
              </div>
            ) : (
              myPosts.map((post) => (
                <ComplaintCard
                  key={post.id || post.complaint_id}
                  id={post.id || post.complaint_id}
                  title={post.title}
                  desc={post.original_text || post.description}
                  summary={post.summary || post.llm_analysis?.summary}
                  category={post.category}
                  has_image={post.has_image}
                  author={post.is_anonymous ? 'Anonymous' : (post.author || post.student_roll_no)}
                  status={post.status}
                  priority={post.priority}
                  upvotes={post.upvotes}
                  timestamp={post.submitted_at || post.created_at}
                  isOwner={true}
                />
              ))
            )}
          </div>
        )}
      </div>

      {user?.role === 'Student' && <BottomNav />}
    </div>
  );
}
