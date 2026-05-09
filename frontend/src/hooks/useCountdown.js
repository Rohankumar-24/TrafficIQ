import { useState, useEffect, useRef } from 'react';

export function useCountdown(initialValue, signal) {
  const [count, setCount] = useState(initialValue);
  const timerRef = useRef(null);
  const prevSignalRef = useRef(signal);

  useEffect(() => {
    // Reset when signal type changes or duration jumps up significantly
    if (signal !== prevSignalRef.current || initialValue > count + 3) {
      setCount(initialValue);
      prevSignalRef.current = signal;
    }
  }, [initialValue, signal]);

  useEffect(() => {
    if (count <= 0) return;

    timerRef.current = setInterval(() => {
      setCount(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timerRef.current);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count === initialValue]);

  return count;
}
