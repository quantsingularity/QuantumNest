// Portfolio Transactions Tab Component
'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
    Table,
    TableHeader,
    TableRow,
    TableHead,
    TableBody,
    TableCell,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '@/lib/utils';

export default function TransactionsTab() {
    const [filter, setFilter] = useState<'all' | 'buy' | 'sell' | 'dividend'>('all');
    const [timeRange, setTimeRange] = useState('30d');

    // Mock transaction data
    const allTransactions = [
        {
            id: 1,
            date: '2025-04-12',
            type: 'Buy',
            asset: 'AAPL',
            assetName: 'Apple Inc.',
            quantity: 10,
            price: 180.25,
            total: 1802.5,
            fees: 5.0,
            status: 'Completed',
        },
        {
            id: 2,
            date: '2025-04-10',
            type: 'Sell',
            asset: 'TSLA',
            assetName: 'Tesla, Inc.',
            quantity: 5,
            price: 210.75,
            total: 1053.75,
            fees: 3.5,
            status: 'Completed',
        },
        {
            id: 3,
            date: '2025-04-08',
            type: 'Dividend',
            asset: 'MSFT',
            assetName: 'Microsoft Corporation',
            quantity: 75,
            price: 0.75,
            total: 56.25,
            fees: 0,
            status: 'Completed',
        },
        {
            id: 4,
            date: '2025-04-05',
            type: 'Buy',
            asset: 'ETH',
            assetName: 'Ethereum',
            quantity: 2.5,
            price: 3200.0,
            total: 8000.0,
            fees: 25.0,
            status: 'Completed',
        },
        {
            id: 5,
            date: '2025-04-02',
            type: 'Buy',
            asset: 'MSFT',
            assetName: 'Microsoft Corporation',
            quantity: 8,
            price: 410.5,
            total: 3284.0,
            fees: 10.0,
            status: 'Completed',
        },
        {
            id: 6,
            date: '2025-03-28',
            type: 'Sell',
            asset: 'BTC',
            assetName: 'Bitcoin',
            quantity: 0.5,
            price: 65000.0,
            total: 32500.0,
            fees: 100.0,
            status: 'Completed',
        },
        {
            id: 7,
            date: '2025-03-25',
            type: 'Buy',
            asset: 'GOOGL',
            assetName: 'Alphabet Inc.',
            quantity: 5,
            price: 2450.0,
            total: 12250.0,
            fees: 35.0,
            status: 'Completed',
        },
        {
            id: 8,
            date: '2025-03-20',
            type: 'Dividend',
            asset: 'VTI',
            assetName: 'Vanguard Total Stock Market ETF',
            quantity: 200,
            price: 0.85,
            total: 170.0,
            fees: 0,
            status: 'Completed',
        },
    ];

    const filteredTransactions = allTransactions.filter((t) => {
        if (filter === 'all') return true;
        return t.type.toLowerCase() === filter;
    });

    const totalBuy = allTransactions
        .filter((t) => t.type === 'Buy')
        .reduce((sum, t) => sum + t.total, 0);
    const totalSell = allTransactions
        .filter((t) => t.type === 'Sell')
        .reduce((sum, t) => sum + t.total, 0);
    const totalDividends = allTransactions
        .filter((t) => t.type === 'Dividend')
        .reduce((sum, t) => sum + t.total, 0);
    const totalFees = allTransactions.reduce((sum, t) => sum + t.fees, 0);

    return (
        <div className="space-y-6">
            {/* Transaction Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-4">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Total Buy</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(totalBuy)}
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Total Sell</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(totalSell)}
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Dividends</p>
                        <p className="text-xl font-bold text-green-600 dark:text-green-400">
                            {formatCurrency(totalDividends)}
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4">
                        <p className="text-sm text-gray-500 dark:text-gray-400">Total Fees</p>
                        <p className="text-xl font-bold text-gray-900 dark:text-white">
                            {formatCurrency(totalFees)}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex flex-wrap gap-2">
                    <Button
                        variant={filter === 'all' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('all')}
                    >
                        All
                    </Button>
                    <Button
                        variant={filter === 'buy' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('buy')}
                    >
                        Buy
                    </Button>
                    <Button
                        variant={filter === 'sell' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('sell')}
                    >
                        Sell
                    </Button>
                    <Button
                        variant={filter === 'dividend' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('dividend')}
                    >
                        Dividend
                    </Button>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant={timeRange === '7d' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setTimeRange('7d')}
                    >
                        7D
                    </Button>
                    <Button
                        variant={timeRange === '30d' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setTimeRange('30d')}
                    >
                        30D
                    </Button>
                    <Button
                        variant={timeRange === '90d' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setTimeRange('90d')}
                    >
                        90D
                    </Button>
                    <Button
                        variant={timeRange === 'all' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setTimeRange('all')}
                    >
                        All
                    </Button>
                </div>
            </div>

            {/* Transactions Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Transaction History</CardTitle>
                </CardHeader>
                <CardContent className="p-0 sm:p-6">
                    <div className="overflow-x-auto">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Asset</TableHead>
                                    <TableHead className="hidden md:table-cell">Quantity</TableHead>
                                    <TableHead className="hidden lg:table-cell">Price</TableHead>
                                    <TableHead>Total</TableHead>
                                    <TableHead className="hidden sm:table-cell">Fees</TableHead>
                                    <TableHead className="hidden xl:table-cell">Status</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredTransactions.map((transaction) => (
                                    <TableRow key={transaction.id}>
                                        <TableCell className="text-sm">
                                            {new Date(transaction.date).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell>
                                            <span
                                                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                                    transaction.type === 'Buy'
                                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                                        : transaction.type === 'Sell'
                                                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                                          : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                                }`}
                                            >
                                                {transaction.type}
                                            </span>
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            <div className="font-semibold">{transaction.asset}</div>
                                            <div className="text-xs text-gray-500 hidden lg:block">
                                                {transaction.assetName}
                                            </div>
                                        </TableCell>
                                        <TableCell className="hidden md:table-cell">
                                            {transaction.quantity}
                                        </TableCell>
                                        <TableCell className="hidden lg:table-cell">
                                            {formatCurrency(transaction.price)}
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {formatCurrency(transaction.total)}
                                        </TableCell>
                                        <TableCell className="hidden sm:table-cell text-gray-500">
                                            {formatCurrency(transaction.fees)}
                                        </TableCell>
                                        <TableCell className="hidden xl:table-cell">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                                                {transaction.status}
                                            </span>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
