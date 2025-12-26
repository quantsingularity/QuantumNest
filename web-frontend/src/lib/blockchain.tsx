'use client';

import React, {
    createContext,
    useContext,
    useState,
    useEffect,
    ReactNode,
    useCallback,
} from 'react';
import { ethers } from 'ethers';

// Extend Window interface for ethereum
declare global {
    interface Window {
        ethereum?: any;
    }
}

// Interface for portfolio asset
export interface PortfolioAsset {
    id: string;
    name: string;
    symbol: string;
    quantity: number;
    value: number;
    tokenAddress?: string;
}

// Interface for transaction data
export interface TransactionData {
    hash: string;
    from: string;
    to: string;
    value: string;
    timestamp: number;
    status: 'pending' | 'confirmed' | 'failed';
    blockNumber?: number;
    gasUsed?: string;
}

interface BlockchainContextType {
    provider: ethers.providers.Web3Provider | null;
    signer: ethers.Signer | null;
    account: string | null;
    chainId: number | null;
    isConnected: boolean;
    isConnecting: boolean;
    error: string | null;
    connectWallet: () => Promise<void>;
    disconnectWallet: () => void;
    getBalance: () => Promise<string>;
    sendTransaction: (to: string, amount: string) => Promise<ethers.providers.TransactionResponse>;
}

const BlockchainContext = createContext<BlockchainContextType | undefined>(undefined);

interface BlockchainProviderProps {
    children: ReactNode;
}

export function BlockchainProvider({ children }: BlockchainProviderProps) {
    const [provider, setProvider] = useState<ethers.providers.Web3Provider | null>(null);
    const [signer, setSigner] = useState<ethers.Signer | null>(null);
    const [account, setAccount] = useState<string | null>(null);
    const [chainId, setChainId] = useState<number | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Initialize provider on mount if already connected
    useEffect(() => {
        if (typeof window !== 'undefined' && window.ethereum) {
            const checkConnection = async () => {
                try {
                    const web3Provider = new ethers.providers.Web3Provider(window.ethereum);
                    const accounts = await web3Provider.listAccounts();

                    if (accounts.length > 0) {
                        setProvider(web3Provider);
                        const web3Signer = web3Provider.getSigner();
                        setSigner(web3Signer);
                        setAccount(accounts[0]);
                        const network = await web3Provider.getNetwork();
                        setChainId(network.chainId);
                        setIsConnected(true);
                    }
                } catch (err) {
                    console.error('Error checking connection:', err);
                }
            };

            checkConnection();

            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts: string[]) => {
                if (accounts.length > 0) {
                    setAccount(accounts[0]);
                    if (provider) {
                        const newSigner = provider.getSigner();
                        setSigner(newSigner);
                    }
                } else {
                    // User disconnected
                    setAccount(null);
                    setSigner(null);
                    setIsConnected(false);
                }
            });

            // Listen for chain changes
            window.ethereum.on('chainChanged', (newChainId: string) => {
                // Reload the page as recommended by MetaMask
                window.location.reload();
            });

            return () => {
                if (window.ethereum.removeListener) {
                    window.ethereum.removeListener('accountsChanged', () => {});
                    window.ethereum.removeListener('chainChanged', () => {});
                }
            };
        }
    }, [provider]);

    const connectWallet = async () => {
        if (typeof window === 'undefined' || !window.ethereum) {
            setError('MetaMask is not installed. Please install MetaMask to use this application.');
            return;
        }

        setIsConnecting(true);
        setError(null);

        try {
            // Request account access
            await window.ethereum.request({ method: 'eth_requestAccounts' });

            const web3Provider = new ethers.providers.Web3Provider(window.ethereum);
            setProvider(web3Provider);

            const web3Signer = web3Provider.getSigner();
            setSigner(web3Signer);

            const address = await web3Signer.getAddress();
            setAccount(address);

            const network = await web3Provider.getNetwork();
            setChainId(network.chainId);

            setIsConnected(true);
        } catch (err: any) {
            console.error('Error connecting wallet:', err);
            setError(err.message || 'Failed to connect wallet');
            setIsConnected(false);
        } finally {
            setIsConnecting(false);
        }
    };

    const disconnectWallet = useCallback(() => {
        setProvider(null);
        setSigner(null);
        setAccount(null);
        setChainId(null);
        setIsConnected(false);
        setError(null);
    }, []);

    const getBalance = async (): Promise<string> => {
        if (!provider || !account) {
            throw new Error('Wallet not connected');
        }

        const balance = await provider.getBalance(account);
        return ethers.utils.formatEther(balance);
    };

    const sendTransaction = async (
        to: string,
        amount: string,
    ): Promise<ethers.providers.TransactionResponse> => {
        if (!signer) {
            throw new Error('Wallet not connected');
        }

        const tx = await signer.sendTransaction({
            to,
            value: ethers.utils.parseEther(amount),
        });

        return tx;
    };

    const value = {
        provider,
        signer,
        account,
        chainId,
        isConnected,
        isConnecting,
        error,
        connectWallet,
        disconnectWallet,
        getBalance,
        sendTransaction,
    };

    return <BlockchainContext.Provider value={value}>{children}</BlockchainContext.Provider>;
}

export function useBlockchain() {
    const context = useContext(BlockchainContext);

    if (context === undefined) {
        throw new Error('useBlockchain must be used within a BlockchainProvider');
    }

    return context;
}
