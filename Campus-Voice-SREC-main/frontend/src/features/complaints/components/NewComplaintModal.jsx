// src/components/NewComplaintModal.jsx
import { useState } from "react";
import { Button, Select } from "../../../components/UI";

export default function NewComplaintModal({ isOpen, onClose, onAdd }) {
  // Category is now AI assigned, removed from manual input
  const [form, setForm] = useState({ title: "", desc: "", img: null });
  const [preview, setPreview] = useState("");

  if (!isOpen) return null;

  const handleImage = (e) => {
    const file = e.target.files[0];
    if (file) {
      setForm({ ...form, img: file });
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title || !form.desc || !form.img) {
      alert("All fields including image are required!");
      return;
    }
    // Mock submit for local feedback in Home (actual logic might differ in Posts.jsx)
    if (onAdd) {
      onAdd({
        ...form,
        img: preview,
        author: "You",
        id: Date.now(),
        status: "Pending",
        // category will be pending/assigned by backend
        category: "Pending AI Analysis",
        upvotes: 0,
        submitted_at: new Date().toISOString()
      });
    }
    setForm({ title: "", desc: "", img: null });
    setPreview("");
    onClose();
  };

  const inputClass = "w-full rounded-lg border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-900 shadow-neu-light placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand/50 transition-all";

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex justify-center items-center p-4 animate-fadeIn">
      <div className="bg-surface rounded-2xl shadow-2xl w-full max-w-lg border border-white/60 p-6 sm:p-8 transform transition-all scale-100">
        <h2 className="text-xl font-bold text-gray-900 mb-6">New Complaint</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              className={inputClass}
              placeholder="Title of your grievance"
              value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })}
            />
          </div>

          <div>
            <textarea
              className={inputClass}
              placeholder="Describe the issue in detail..."
              rows={4}
              value={form.desc}
              onChange={e => setForm({ ...form, desc: e.target.value })}
            ></textarea>
          </div>

          {/* Category selection removed - AI handled */}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Upload Evidence</label>
            <div className="flex items-center justify-center w-full">
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <svg className="w-8 h-8 mb-3 text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                    <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2" />
                  </svg>
                  <p className="text-xs text-gray-500"><span className="font-semibold">Click to upload</span> image</p>
                </div>
                <input type="file" className="hidden" accept="image/*" onChange={handleImage} />
              </label>
            </div>
            {preview && (
              <div className="mt-3 relative h-32 w-full rounded-lg overflow-hidden border border-gray-200">
                <img src={preview} alt="preview" className="w-full h-full object-cover" />
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" variant="primary">Post Grievance</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
