import React from 'react';
import { render, screen } from '@testing-library/react';
import Home from '../page';

// Mock the counter module
jest.mock('../counter', () => ({
    getStats: jest.fn(() =>
        Promise.resolve({
            count: 5,
            recentAccess: [
                { accessed_at: '2025-04-13T10:00:00Z' },
                { accessed_at: '2025-04-13T09:00:00Z' },
            ],
        }),
    ),
    incrementAndLog: jest.fn(() =>
        Promise.resolve({
            count: 6,
            recentAccess: [
                { accessed_at: '2025-04-13T11:00:00Z' },
                { accessed_at: '2025-04-13T10:00:00Z' },
            ],
        }),
    ),
}));

describe('Home Page', () => {
    it('renders the home page', () => {
        render(<Home />);
        expect(screen.getByText(/Views:/i)).toBeInTheDocument();
    });

    it('displays the increment button', () => {
        render(<Home />);
        expect(screen.getByRole('button', { name: /increment/i })).toBeInTheDocument();
    });
});
