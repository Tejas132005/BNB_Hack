/**
 * NeutraYield AI - Global Wallet Manager
 * =======================================
 * Handles MetaMask connection, network validation, and wallet state.
 * NEVER accesses or stores private keys.
 */

// BNB Testnet Configuration
const BNB_TESTNET = {
    chainId: '0x61',         // 97 in hex
    chainIdDecimal: 97,
    chainName: 'BNB Smart Chain Testnet',
    nativeCurrency: {
        name: 'tBNB',
        symbol: 'tBNB',
        decimals: 18,
    },
    rpcUrls: ['https://data-seed-prebsc-1-s1.binance.org:8545/'],
    blockExplorerUrls: ['https://testnet.bscscan.com/'],
};

// Global wallet state
window.NeutraYield = {
    isAgentRunning: true,
    activeStrategy: 'MODERATE',
    wallet: {
        connected: false,
        address: null,
        chainId: null,
        isCorrectNetwork: false,
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const connectBtn = document.getElementById('connectWallet');
    const walletBtnText = document.getElementById('walletBtnText');
    const networkBadge = document.getElementById('networkBadge');
    const networkName = document.getElementById('networkName');
    const networkModal = document.getElementById('networkModal');
    const switchNetworkBtn = document.getElementById('switchNetworkBtn');
    const closeNetworkModal = document.getElementById('closeNetworkModal');

    // ── Utility: Shorten address ──
    function shortenAddress(addr) {
        return addr.substring(0, 6) + '...' + addr.substring(addr.length - 4);
    }

    // ── Update UI based on wallet state ──
    function updateWalletUI() {
        const w = window.NeutraYield.wallet;
        if (w.connected && w.address) {
            walletBtnText.textContent = shortenAddress(w.address);
            connectBtn.classList.add('connected');
            connectBtn.title = w.address;

            networkBadge.style.display = 'flex';
            if (w.isCorrectNetwork) {
                networkName.textContent = 'BNB Testnet';
                networkBadge.classList.remove('wrong-network');
                networkBadge.classList.add('correct-network');
            } else {
                networkName.textContent = 'Wrong Network';
                networkBadge.classList.remove('correct-network');
                networkBadge.classList.add('wrong-network');
            }
        } else {
            walletBtnText.textContent = 'Connect Wallet';
            connectBtn.classList.remove('connected');
            connectBtn.title = '';
            networkBadge.style.display = 'none';
        }

        // Dispatch custom event for other pages to react
        window.dispatchEvent(new CustomEvent('walletStateChanged', { detail: w }));
    }

    // ── Check if correct network ──
    function checkNetwork(chainId) {
        const hexChainId = typeof chainId === 'string' ? chainId : '0x' + chainId.toString(16);
        return hexChainId.toLowerCase() === BNB_TESTNET.chainId.toLowerCase();
    }

    // ── Connect Wallet ──
    async function connectWallet() {
        if (typeof window.ethereum === 'undefined') {
            showNotification('MetaMask not detected. Please install MetaMask to use NeutraYield AI.', 'error');
            return;
        }

        try {
            walletBtnText.textContent = 'Connecting...';
            connectBtn.disabled = true;

            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });

            window.NeutraYield.wallet = {
                connected: true,
                address: accounts[0],
                chainId: chainId,
                isCorrectNetwork: checkNetwork(chainId),
            };

            updateWalletUI();

            if (!window.NeutraYield.wallet.isCorrectNetwork) {
                networkModal.style.display = 'flex';
            } else {
                showNotification(
                    `✅ Wallet connected: ${shortenAddress(accounts[0])}<br>Network: BNB Chain Testnet`,
                    'success'
                );
            }
        } catch (error) {
            console.error('Wallet connection failed:', error);
            if (error.code === 4001) {
                showNotification('Connection rejected by user.', 'error');
            } else {
                showNotification('Failed to connect wallet. Please try again.', 'error');
            }
        } finally {
            connectBtn.disabled = false;
        }
    }

    // ── Switch Network ──
    async function switchToBNBTestnet() {
        if (typeof window.ethereum === 'undefined') return;

        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: BNB_TESTNET.chainId }],
            });
            networkModal.style.display = 'none';
        } catch (switchError) {
            // Chain not added to MetaMask — add it
            if (switchError.code === 4902) {
                try {
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: BNB_TESTNET.chainId,
                            chainName: BNB_TESTNET.chainName,
                            nativeCurrency: BNB_TESTNET.nativeCurrency,
                            rpcUrls: BNB_TESTNET.rpcUrls,
                            blockExplorerUrls: BNB_TESTNET.blockExplorerUrls,
                        }],
                    });
                    networkModal.style.display = 'none';
                } catch (addError) {
                    showNotification('Failed to add BNB Testnet. Please add it manually.', 'error');
                }
            } else {
                showNotification('Failed to switch network. Please switch manually in MetaMask.', 'error');
            }
        }
    }

    // ── Event Listeners ──
    if (connectBtn) {
        connectBtn.addEventListener('click', async () => {
            if (window.NeutraYield.wallet.connected) {
                // Already connected — show address info or disconnect
                const address = window.NeutraYield.wallet.address;
                const chainOk = window.NeutraYield.wallet.isCorrectNetwork;
                if (!chainOk) {
                    networkModal.style.display = 'flex';
                } else {
                    showNotification(`Connected: ${shortenAddress(address)}<br>Network: BNB Testnet ✅`, 'success');
                }
            } else {
                await connectWallet();
            }
        });
    }

    if (switchNetworkBtn) {
        switchNetworkBtn.addEventListener('click', switchToBNBTestnet);
    }

    if (closeNetworkModal) {
        closeNetworkModal.addEventListener('click', () => {
            networkModal.style.display = 'none';
        });
    }

    // ── Listen for MetaMask events ──
    if (typeof window.ethereum !== 'undefined') {
        // Account changed
        window.ethereum.on('accountsChanged', (accounts) => {
            if (accounts.length === 0) {
                window.NeutraYield.wallet = {
                    connected: false,
                    address: null,
                    chainId: null,
                    isCorrectNetwork: false,
                };
                showNotification('Wallet disconnected.', 'info');
            } else {
                window.NeutraYield.wallet.address = accounts[0];
                window.NeutraYield.wallet.connected = true;
                showNotification(`Switched to ${shortenAddress(accounts[0])}`, 'info');
            }
            updateWalletUI();
        });

        // Chain changed
        window.ethereum.on('chainChanged', (chainId) => {
            window.NeutraYield.wallet.chainId = chainId;
            window.NeutraYield.wallet.isCorrectNetwork = checkNetwork(chainId);
            updateWalletUI();

            if (window.NeutraYield.wallet.isCorrectNetwork) {
                networkModal.style.display = 'none';
                showNotification('✅ Switched to BNB Chain Testnet', 'success');
            } else {
                showNotification('⚠️ Wrong network detected. Please switch to BNB Testnet.', 'error');
                if (window.NeutraYield.wallet.connected) {
                    networkModal.style.display = 'flex';
                }
            }
        });

        // Auto-reconnect if already connected
        window.ethereum.request({ method: 'eth_accounts' }).then(accounts => {
            if (accounts.length > 0) {
                window.ethereum.request({ method: 'eth_chainId' }).then(chainId => {
                    window.NeutraYield.wallet = {
                        connected: true,
                        address: accounts[0],
                        chainId: chainId,
                        isCorrectNetwork: checkNetwork(chainId),
                    };
                    updateWalletUI();
                });
            }
        }).catch(() => { });
    }
});

// ── Toast Notification (global) ──
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}`;
    toast.innerHTML = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}
