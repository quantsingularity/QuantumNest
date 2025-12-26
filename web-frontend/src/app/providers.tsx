'use client';

import { ApiProvider } from '@/lib/api';
import { BlockchainProvider } from '@/lib/blockchain';
import { AuthProvider } from './auth/AuthContext';

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <ApiProvider>
                <BlockchainProvider>{children}</BlockchainProvider>
            </ApiProvider>
        </AuthProvider>
    );
}
