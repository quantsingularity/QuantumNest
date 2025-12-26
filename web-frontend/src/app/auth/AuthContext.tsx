'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useApi } from '@/lib/api';

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    error: string | null;
    login: (email: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
}

interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const { setToken, token } = useApi();

    useEffect(() => {
        // Check if user is already logged in by checking token
        if (token && !user) {
            // TODO: Implement /users/me endpoint in backend to fetch current user
            // For now, we'll just mark as authenticated if token exists
        }
    }, [token, user]);

    const login = async (email: string, password: string) => {
        try {
            setIsLoading(true);
            setError(null);

            // Create form data for OAuth2 password flow
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/token`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString(),
                },
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            setToken(data.access_token);

            // Set basic user info (in a real app, fetch from /users/me)
            setUser({
                id: 1,
                username: email.split('@')[0],
                email: email,
                is_active: true,
            });

            router.push('/dashboard');
        } catch (error) {
            console.error('Login error:', error);
            setError(error instanceof Error ? error.message : 'Login failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (username: string, email: string, password: string) => {
        try {
            setIsLoading(true);
            setError(null);

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, email, password }),
                },
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Registration failed');
            }

            const userData = await response.json();

            // After successful registration, log the user in
            await login(email, password);
        } catch (error) {
            console.error('Registration error:', error);
            setError(
                error instanceof Error ? error.message : 'Registration failed. Please try again.',
            );
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        router.push('/');
    };

    const value = {
        user,
        isLoading,
        error,
        login,
        register,
        logout,
        isAuthenticated: !!user || !!token,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
