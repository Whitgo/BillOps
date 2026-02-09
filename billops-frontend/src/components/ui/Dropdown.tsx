/**
 * Reusable Dropdown component
 */

import { useState, useRef, useEffect } from 'react';
import type { ReactNode } from 'react';
import clsx from 'clsx';

interface DropdownItem {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

interface DropdownProps {
  trigger: ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
}

export const Dropdown = ({ trigger, items, align = 'left' }: DropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button type="button" onClick={() => setIsOpen((open) => !open)}>
        {trigger}
      </button>
      {isOpen && (
        <div
          className={clsx(
            'absolute mt-2 w-48 rounded-lg bg-white shadow-lg border border-gray-200 z-50',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          <div className="py-1">
            {items.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => {
                  if (!item.disabled) {
                    item.onClick();
                    setIsOpen(false);
                  }
                }}
                disabled={item.disabled}
                className={clsx(
                  'w-full text-left px-4 py-2 text-sm',
                  item.disabled
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
