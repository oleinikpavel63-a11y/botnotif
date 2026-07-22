import { haptics } from '../lib/telegram';

/** Convenience hook exposing the Telegram haptic feedback helpers. */
export function useHaptics(): typeof haptics {
  return haptics;
}
