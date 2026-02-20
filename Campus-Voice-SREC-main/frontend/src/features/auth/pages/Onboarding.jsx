import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/UI';

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
    <div className="min-h-screen bg-background flex items-center justify-center px-4 transition-colors duration-300">
      <div className="w-full max-w-[400px]">
        <div className="bg-surface border border-white/60 rounded-2xl shadow-neu-flat p-10 text-center overflow-hidden">
          <div className="transition-all duration-500 ease-in-out py-8">
            <div className="text-7xl mb-6 select-none animate-pulse drop-shadow-sm">{slides[idx].icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 leading-tight">{slides[idx].title}</h2>
          </div>

          <div className="flex items-center justify-center gap-2 mt-4 mb-8">
            {slides.map((_, i) => (
              <span key={i} className={`h-2.5 w-2.5 rounded-full transition-all duration-300 ${i === idx ? 'bg-brand scale-110' : 'bg-gray-200'}`} />
            ))}
          </div>

          <Button
            onClick={next}
            aria-label={isLast ? 'Get Started' : 'Next slide'}
            className="w-full py-3 text-base shadow-lg shadow-brand/20"
          >
            {isLast ? 'Get Started' : 'Next'}
          </Button>
        </div>
        <button className="text-center text-xs text-gray-400 mt-6 w-full hover:text-gray-600 transition-colors">
          You can change preferences later
        </button>
      </div>
    </div>
  );
}

