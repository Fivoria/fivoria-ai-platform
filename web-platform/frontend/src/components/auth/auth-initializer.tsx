'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/state/store';
import { apiClient } from '@/lib/api-client';

export function AuthInitializer() {
  const token = useAuthStore((state) => state.token);

  useEffect(() => {
    if (token) {
      apiClient.setToken(token);
    } else {
      apiClient.clearToken();
    }
  }, [token]);

  return null;
}
