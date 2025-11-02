import { Toaster } from 'react-hot-toast';

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: { fontSize: '14px' },
        success: { iconTheme: { primary: '#16a34a', secondary: 'white' } },
        error: { iconTheme: { primary: '#dc2626', secondary: 'white' } }
      }}
    />
  );
}

export default ToastProvider;


