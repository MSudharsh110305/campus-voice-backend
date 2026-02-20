import React, { useEffect, useState } from 'react';

export default function InstallPrompt() {
  const [deferredEvent, setDeferredEvent] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredEvent(e);
      setVisible(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  if (!visible) return null;

  const onInstall = async () => {
    if (!deferredEvent) return;
    deferredEvent.prompt();
    await deferredEvent.userChoice;
    setVisible(false);
    setDeferredEvent(null);
  };

  return (
    <div className="fixed bottom-4 inset-x-0 px-4">
      <div className="mx-auto max-w-md bg-white border border-gray-200 shadow-lg rounded-xl p-3 flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-gray-900">Install Campus Voice</div>
          <div className="text-xs text-gray-600">Add to your home screen for quick access.</div>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setVisible(false)} className="text-sm text-gray-600">Later</button>
          <button onClick={onInstall} className="text-sm bg-srec-primary hover:bg-srec-primaryHover text-white px-3 py-1.5 rounded-lg">Install</button>
        </div>
      </div>
    </div>
  );
}
