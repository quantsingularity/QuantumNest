import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Home from './page';

// Mock the hooks
jest.mock('@/lib/api', () => ({
    useApi: () => ({
        get: jest.fn().mockResolvedValue({ status: 'healthy' }),
        isLoading: false,
    }),
}));

jest.mock('@/lib/blockchain', () => ({
    useBlockchain: () => ({
        connectWallet: jest.fn(),
        isConnected: false,
        account: null,
        isConnecting: false,
        error: null,
    }),
}));

jest.mock('@/components/layout/Navbar', () => {
    return function Navbar() {
        return <div data-testid="navbar">Navbar</div>;
    };
});

jest.mock('@/components/ui/Button', () => ({
    Button: ({ children, ...props }: any) => (
        <button data-testid="button" {...props}>
            {children}
        </button>
    ),
}));

jest.mock('@/components/ui/Card', () => ({
    Card: ({ children }: any) => <div data-testid="card">{children}</div>,
    CardHeader: ({ children }: any) => <div>{children}</div>,
    CardTitle: ({ children }: any) => <h3>{children}</h3>,
    CardContent: ({ children }: any) => <div>{children}</div>,
}));

describe('Home Page', () => {
    it('renders the main heading', () => {
        render(<Home />);
        expect(screen.getByText('Welcome to QuantumNest Capital')).toBeInTheDocument();
    });

    it('renders the navbar', () => {
        render(<Home />);
        expect(screen.getByTestId('navbar')).toBeInTheDocument();
    });

    it('displays connect wallet button when not connected', () => {
        render(<Home />);
        expect(screen.getByText('Connect Wallet to Get Started')).toBeInTheDocument();
    });

    it('renders feature cards', async () => {
        render(<Home />);

        await waitFor(() => {
            expect(screen.getByText('AI-Powered Analysis')).toBeInTheDocument();
            expect(screen.getByText('Blockchain Integration')).toBeInTheDocument();
            expect(screen.getByText('Data Science')).toBeInTheDocument();
        });
    });
});
