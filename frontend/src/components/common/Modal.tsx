import { Fragment, PropsWithChildren } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ModalProps {
  title: string;
  open: boolean;
  onClose: () => void;
}

export function Modal({ title, open, onClose, children }: PropsWithChildren<ModalProps>) {
  if (!open) return null;

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative" style={{ zIndex: 9999 }} onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" style={{ zIndex: 9998 }} />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 overflow-y-auto" style={{ zIndex: 9999 }}>
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 translate-y-4 scale-95"
              enterTo="opacity-100 translate-y-0 scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 translate-y-0 scale-100"
              leaveTo="opacity-0 translate-y-4 scale-95"
            >
              <Dialog.Panel className="relative w-full max-w-lg transform overflow-visible rounded-2xl border border-white/40 bg-white p-6 shadow-2xl">
                <div className="flex items-start justify-between mb-4">
                  <Dialog.Title className="text-xl font-display text-ink">{title}</Dialog.Title>
                  <button 
                    className="rounded-lg p-1.5 text-ink/50 hover:bg-ink/5 hover:text-ink transition-colors" 
                    onClick={onClose}
                    type="button"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
                <div>{children}</div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}

export default Modal;


