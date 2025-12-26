'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ApiContextType {
    apiUrl: string;
    token: string | null;
    isLoading: boolean;
    error: string | null;
    setToken: (token: string | null) => void;
    get: <T>(endpoint: string) => Promise<T>;
    post: <T>(endpoint: string, data: any) => Promise<T>;
    put: <T>(endpoint: string, data: any) => Promise<T>;
    delete: <T>(endpoint: string) => Promise<T>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

interface ApiProviderProps {
    children: ReactNode;
}

export function ApiProvider({ children }: ApiProviderProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [token, setTokenState] = useState<string | null>(null);

    // Get API URL from environment or default to localhost
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Load token from localStorage on mount
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const savedToken = localStorage.getItem('auth_token');
            if (savedToken) {
                setTokenState(savedToken);
            }
        }
    }, []);

    const setToken = (newToken: string | null) => {
        setTokenState(newToken);
        if (typeof window !== 'undefined') {
            if (newToken) {
                localStorage.setItem('auth_token', newToken);
            } else {
                localStorage.removeItem('auth_token');
            }
        }
    };

    const getHeaders = () => {
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    };

    const handleResponse = async (response: Response) => {
        setIsLoading(false);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage =
                errorData.detail ||
                errorData.message ||
                `Error: ${response.status} ${response.statusText}`;
            setError(errorMessage);
            throw new Error(errorMessage);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return {} as any;
        }

        return response.json();
    };

    const get = async <T,>(endpoint: string): Promise<T> => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${apiUrl}${endpoint}`, {
                method: 'GET',
                headers: getHeaders(),
            });

            return handleResponse(response);
        } catch (err) {
            setIsLoading(false);
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setError(errorMessage);
            throw err;
        }
    };

    const post = async <T,>(endpoint: string, data: any): Promise<T> => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${apiUrl}${endpoint}`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(data),
            });

            return handleResponse(response);
        } catch (err) {
            setIsLoading(false);
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setError(errorMessage);
            throw err;
        }
    };

    const put = async <T,>(endpoint: string, data: any): Promise<T> => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${apiUrl}${endpoint}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(data),
            });

            return handleResponse(response);
        } catch (err) {
            setIsLoading(false);
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setError(errorMessage);
            throw err;
        }
    };

    const deleteRequest = async <T,>(endpoint: string): Promise<T> => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${apiUrl}${endpoint}`, {
                method: 'DELETE',
                headers: getHeaders(),
            });

            return handleResponse(response);
        } catch (err) {
            setIsLoading(false);
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setError(errorMessage);
            throw err;
        }
    };

    const value = {
        apiUrl,
        token,
        isLoading,
        error,
        setToken,
        get,
        post,
        put,
        delete: deleteRequest,
    };

    return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

export function useApi() {
    const context = useContext(ApiContext);

    if (context === undefined) {
        throw new Error('useApi must be used within an ApiProvider');
    }

    return context;
}
