import { renderHook } from '@testing-library/react';
import { ApiProvider, useApi } from '../api';
import React from 'react';

global.fetch = jest.fn();

describe('API Context', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('provides API methods', () => {
        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <ApiProvider>{children}</ApiProvider>
        );
        const { result } = renderHook(() => useApi(), { wrapper });

        expect(result.current).toHaveProperty('get');
        expect(result.current).toHaveProperty('post');
        expect(result.current).toHaveProperty('put');
        expect(result.current).toHaveProperty('delete');
    });

    it('throws error when used outside provider', () => {
        expect(() => {
            renderHook(() => useApi());
        }).toThrow('useApi must be used within an ApiProvider');
    });
});
