// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ArbitrageVault
 * @dev Simple vault to record arbitrage trades on BNB Chain.
 */
contract ArbitrageVault {
    address public owner;
    uint256 public totalTrades;
    
    event TradeExecuted(address indexed user, string action, uint256 amount, uint256 timestamp);
    event FundsWithdrawn(address indexed owner, uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    /**
     * @dev Records a BUY action (e.g., locking funds for a position)
     */
    function buy() external payable {
        require(msg.value > 0, "Must send BNB to record a trade");
        totalTrades++;
        emit TradeExecuted(msg.sender, "BUY", msg.value, block.timestamp);
    }

    /**
     * @dev Records a SELL action and sends funds back to the user/owner
     */
    function sell(uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Insufficient balance in vault");
        totalTrades++;
        payable(owner).transfer(amount);
        emit TradeExecuted(owner, "SELL", amount, block.timestamp);
    }

    /**
     * @dev Emergency stop or repositioning
     */
    function stop() external onlyOwner {
        emit TradeExecuted(owner, "STOP", 0, block.timestamp);
    }

    /**
     * @dev Withdraw all funds from the vault
     */
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        payable(owner).transfer(balance);
        emit FundsWithdrawn(owner, balance);
    }

    function getPosition() external view returns (uint256) {
        return address(this).balance;
    }

    receive() external payable {}
}
