'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/layout/Navbar';
import { StatCard } from '@/components/ui/Cards';
import { LineChart, DoughnutChart } from '@/components/ui/Charts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
    Table,
    TableHeader,
    TableRow,
    TableHead,
    TableBody,
    TableCell,
} from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { formatCurrency } from '@/lib/utils';
import { useApi } from '@/lib/api';
import { useBlockchain } from '@/lib/blockchain';

interface PortfolioAsset {
    id: string;
    symbol: string;
    name: string;
    quantity: number;
    averagePrice: number;
    currentPrice: number;
    totalValue: number;
    profitLoss: number;
    profitLossPercentage: number;
}

export default function Portfolio() {
    const { get, isLoading } = useApi();
    const { account, isConnected } = useBlockchain();
    const [assets, setAssets] = useState<PortfolioAsset[]>([]);
    const [loadingAssets, setLoadingAssets] = useState(true);

    useEffect(() => {
        const fetchPortfolio = async () => {
            try {
                setLoadingAssets(true);
                // Try to fetch from backend API
                const data = await get<{ assets: PortfolioAsset[] }>('/portfolio/assets');
                setAssets(data.assets || []);
            } catch (error) {
                console.error('Error fetching portfolio:', error);
                // Use mock data if API fails
                setAssets(getMockAssets());
            } finally {
                setLoadingAssets(false);
            }
        };

        fetchPortfolio();
    }, [get]);

    const getMockAssets = (): PortfolioAsset[] => [
        {
            id: '1',
            symbol: 'AAPL',
            name: 'Apple Inc.',
            quantity: 50,
            averagePrice: 150.0,
            currentPrice: 180.25,
            totalValue: 9012.5,
            profitLoss: 1512.5,
            profitLossPercentage: 20.17,
        },
        {
            id: '2',
            symbol: 'TSLA',
            name: 'Tesla, Inc.',
            quantity: 25,
            averagePrice: 200.0,
            currentPrice: 210.75,
            totalValue: 5268.75,
            profitLoss: 268.75,
            profitLossPercentage: 5.38,
        },
        {
            id: '3',
            symbol: 'ETH',
            name: 'Ethereum',
            quantity: 10,
            averagePrice: 3000.0,
            currentPrice: 3200.0,
            totalValue: 32000.0,
            profitLoss: 2000.0,
            profitLossPercentage: 6.67,
        },
        {
            id: '4',
            symbol: 'MSFT',
            name: 'Microsoft Corporation',
            quantity: 30,
            averagePrice: 400.0,
            currentPrice: 410.5,
            totalValue: 12315.0,
            profitLoss: 315.0,
            profitLossPercentage: 2.63,
        },
        {
            id: '5',
            symbol: 'GOOGL',
            name: 'Alphabet Inc.',
            quantity: 20,
            averagePrice: 140.0,
            currentPrice: 142.5,
            totalValue: 2850.0,
            profitLoss: 50.0,
            profitLossPercentage: 1.79,
        },
    ];

    const totalValue = assets.reduce((sum, asset) => sum + asset.totalValue, 0);
    const totalProfitLoss = assets.reduce((sum, asset) => sum + asset.profitLoss, 0);
    const totalProfitLossPercentage =
        totalValue > 0 ? (totalProfitLoss / (totalValue - totalProfitLoss)) * 100 : 0;

    const allocationData = {
        labels: assets.map((asset) => asset.symbol),
        datasets: [
            {
                data: assets.map((asset) => asset.totalValue),
                backgroundColor: [
                    'rgba(99, 102, 241, 0.8)',
                    'rgba(79, 70, 229, 0.8)',
                    'rgba(67, 56, 202, 0.8)',
                    'rgba(55, 48, 163, 0.8)',
                    'rgba(49, 46, 129, 0.8)',
                ],
                borderColor: [
                    'rgba(99, 102, 241, 1)',
                    'rgba(79, 70, 229, 1)',
                    'rgba(67, 56, 202, 1)',
                    'rgba(55, 48, 163, 1)',
                    'rgba(49, 46, 129, 1)',
                ],
                borderWidth: 1,
            },
        ],
    };

    const performanceData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
            {
                label: 'Portfolio Value',
                data: [50000, 52000, 55000, 54000, 59000, totalValue],
                borderColor: 'rgba(99, 102, 241, 1)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                fill: true,
            },
        ],
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <main className="container mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Portfolio</h1>
                    <Button>Add Asset</Button>
                </div>

                {!isConnected && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
                        <p className="text-yellow-800 dark:text-yellow-300">
                            Connect your wallet to view blockchain-based assets and perform
                            transactions.
                        </p>
                    </div>
                )}

                {/* Stats Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <StatCard
                        title="Total Value"
                        value={formatCurrency(totalValue)}
                        change={totalProfitLossPercentage}
                        description="Overall P&L"
                    />
                    <StatCard title="Total Assets" value={assets.length} />
                    <StatCard
                        title="Profit/Loss"
                        value={formatCurrency(totalProfitLoss)}
                        change={totalProfitLossPercentage}
                        description={`${totalProfitLossPercentage >= 0 ? '+' : ''}${totalProfitLossPercentage.toFixed(2)}%`}
                    />
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    <div className="lg:col-span-2">
                        <LineChart
                            data={performanceData}
                            title="Portfolio Performance"
                            height={350}
                        />
                    </div>
                    <div>
                        <DoughnutChart
                            data={allocationData}
                            title="Asset Allocation"
                            height={350}
                        />
                    </div>
                </div>

                {/* Assets Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Your Assets</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loadingAssets ? (
                            <div className="flex justify-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                            </div>
                        ) : assets.length === 0 ? (
                            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                                No assets in your portfolio. Add your first asset to get started.
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Symbol</TableHead>
                                            <TableHead>Name</TableHead>
                                            <TableHead>Quantity</TableHead>
                                            <TableHead>Avg. Price</TableHead>
                                            <TableHead>Current Price</TableHead>
                                            <TableHead>Total Value</TableHead>
                                            <TableHead>P&L</TableHead>
                                            <TableHead>P&L %</TableHead>
                                            <TableHead>Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {assets.map((asset) => (
                                            <TableRow key={asset.id}>
                                                <TableCell className="font-bold">
                                                    {asset.symbol}
                                                </TableCell>
                                                <TableCell>{asset.name}</TableCell>
                                                <TableCell>{asset.quantity}</TableCell>
                                                <TableCell>
                                                    {formatCurrency(asset.averagePrice)}
                                                </TableCell>
                                                <TableCell>
                                                    {formatCurrency(asset.currentPrice)}
                                                </TableCell>
                                                <TableCell className="font-medium">
                                                    {formatCurrency(asset.totalValue)}
                                                </TableCell>
                                                <TableCell
                                                    className={
                                                        asset.profitLoss >= 0
                                                            ? 'text-green-600 dark:text-green-400'
                                                            : 'text-red-600 dark:text-red-400'
                                                    }
                                                >
                                                    {formatCurrency(asset.profitLoss)}
                                                </TableCell>
                                                <TableCell
                                                    className={
                                                        asset.profitLossPercentage >= 0
                                                            ? 'text-green-600 dark:text-green-400'
                                                            : 'text-red-600 dark:text-red-400'
                                                    }
                                                >
                                                    {asset.profitLossPercentage >= 0 ? '+' : ''}
                                                    {asset.profitLossPercentage.toFixed(2)}%
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex gap-2">
                                                        <Button size="sm" variant="outline">
                                                            Buy
                                                        </Button>
                                                        <Button size="sm" variant="outline">
                                                            Sell
                                                        </Button>
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
