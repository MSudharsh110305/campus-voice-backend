import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const slides = [
  {
    title: 'Report campus issues easily & anonymously.',
    icon: '📝',
  },
  {
    title: 'Track progress transparently with real-time updates.',
    icon: '📈',
  },
  {
    title: 'Your voice matters – make SREC better.',
    icon: '🎓',
  },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const [idx, setIdx] = useState(0);
  const isLast = useMemo(() => idx === slides.length - 1, [idx]);

  const next = () => {
    if (isLast) {
      localStorage.setItem('onboarded', 'true');
      localStorage.removeItem('cv_last_tab');
      navigate('/login');
    } else {
      setIdx((i) => Math.min(i + 1, slides.length - 1));
    }
  };

  return (
    <div className="min-h-screen bg-srec-background flex items-center justify-center px-4">
      <div className="w-full max-w-[380px]">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-srec-primary tracking-tight">CampusVoice</h1>
        </div>

        <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-10 text-center">
          <div className="transition-all duration-500 ease-in-out py-6">
            <div className="text-6xl mb-6 select-none drop-shadow-sm">{slides[idx].icon}</div>
            <h2 className="text-xl font-bold text-gray-900 leading-snug">{slides[idx].title}</h2>
          </div>

          {/* Dots */}
          <div className="flex items-center justify-center gap-2 mb-8">
            {slides.map((_, i) => (
              <span
                key={i}
                className={`h-2 rounded-full transition-all duration-300 ${
                  i === idx ? 'w-6 bg-srec-primary' : 'w-2 bg-gray-200'
                }`}
              />
            ))}
          </div>

          <button
            onClick={next}
            aria-label={isLast ? 'Get Started' : 'Next slide'}
            className="w-full py-3.5 bg-srec-primary text-white font-semibold rounded-xl hover:bg-srec-primaryHover transition-all duration-200 shadow-sm text-base"
          >
            {isLast ? 'Get Started' : 'Next'}
          </button>
        </div>

        <button
          onClick={() => { localStorage.setItem('onboarded', 'true'); navigate('/login'); }}
          className="text-center text-xs text-gray-400 mt-4 w-full hover:text-gray-600 transition-colors"
        >
          Skip
        </button>
      </div>
    </div>
  );
}
