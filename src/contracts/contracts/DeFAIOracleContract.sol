// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DeFAIOracleContract
 * @notice On-chain sentiment oracle for Base memecoins
 * @dev Stores and manages sentiment scores for tokens
 */

contract DeFAIOracleContract {
    
    // ============================================
    // Data Structures
    // ============================================
    
    struct SentimentData {
        uint256 score;              // 0-10000 (represents 0-100%)
        uint256 confidence;         // 0-10000
        uint256 timestamp;
        uint256 numSubmissions;
    }
    
    struct OracleNode {
        address nodeAddress;
        string nodeName;
        bool isActive;
        uint256 totalSubmissions;
        uint256 lastSubmissionTime;
    }
    
    // ============================================
    // State Variables
    // ============================================
    
    // Sentiment scores for tokens
    mapping(address => SentimentData) public sentimentScores;
    
    // Historical sentiment data
    mapping(address => SentimentData[]) public historicalData;
    
    // Authorized oracle nodes
    mapping(address => bool) public authorizedNodes;
    
    // Oracle node details
    mapping(address => OracleNode) public oracleNodes;
    
    // Owner
    address public owner;
    
    // Update frequency
    uint256 public updateFrequency = 5 minutes;
    
    // Supported tokens
    address[] public supportedTokens;
    mapping(address => bool) public isSupportedToken;
    
    // ============================================
    // Events
    // ============================================
    
    event SentimentUpdated(
        address indexed token,
        uint256 score,
        uint256 confidence,
        uint256 timestamp
    );
    
    event NodeAuthorized(address indexed node, string nodeName);
    event NodeRevoked(address indexed node);
    event TokenAdded(address indexed token);
    event TokenRemoved(address indexed token);
    
    // ============================================
    // Modifiers
    // ============================================
    
    modifier onlyAuthorizedNode() {
        require(authorizedNodes[msg.sender], "Not authorized");
        _;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    // ============================================
    // Constructor
    // ============================================
    
    constructor() {
        owner = msg.sender;
    }
    
    // ============================================
    // Public Functions - Sentiment Queries
    // ============================================
    
    /**
     * @notice Get current sentiment score for a token
     * @param tokenAddress Address of the token
     * @return score Sentiment score (0-10000)
     * @return confidence Confidence level (0-10000)
     * @return timestamp Last update timestamp
     */
    function getSentimentScore(address tokenAddress)
        external
        view
        returns (uint256 score, uint256 confidence, uint256 timestamp)
    {
        SentimentData memory data = sentimentScores[tokenAddress];
        return (data.score, data.confidence, data.timestamp);
    }
    
    /**
     * @notice Get historical sentiment data for a token
     * @param tokenAddress Address of the token
     * @param lookbackHours Number of hours to look back
     * @return Array of historical sentiment data
     */
    function getHistoricalSentiment(address tokenAddress, uint256 lookbackHours)
        external
        view
        returns (SentimentData[] memory)
    {
        uint256 cutoffTime = block.timestamp - (lookbackHours * 1 hours);
        SentimentData[] memory history = historicalData[tokenAddress];
        
        // Count matching entries
        uint256 count = 0;
        for (uint256 i = 0; i < history.length; i++) {
            if (history[i].timestamp >= cutoffTime) {
                count++;
            }
        }
        
        // Create result array
        SentimentData[] memory result = new SentimentData[](count);
        uint256 resultIndex = 0;
        
        for (uint256 i = 0; i < history.length; i++) {
            if (history[i].timestamp >= cutoffTime) {
                result[resultIndex] = history[i];
                resultIndex++;
            }
        }
        
        return result;
    }
    
    /**
     * @notice Get all supported tokens
     * @return Array of supported token addresses
     */
    function getSupportedTokens() external view returns (address[] memory) {
        return supportedTokens;
    }
    
    // ============================================
    // Public Functions - Oracle Submissions
    // ============================================
    
    /**
     * @notice Submit sentiment data (oracle nodes only)
     * @param tokenAddress Address of the token
     * @param score Sentiment score (0-10000)
     * @param confidence Confidence level (0-10000)
     */
    function submitSentimentData(
        address tokenAddress,
        uint256 score,
        uint256 confidence
    ) external onlyAuthorizedNode {
        require(score <= 10000, "Invalid score");
        require(confidence <= 10000, "Invalid confidence");
        require(isSupportedToken[tokenAddress], "Token not supported");
        
        // Update current sentiment
        sentimentScores[tokenAddress] = SentimentData({
            score: score,
            confidence: confidence,
            timestamp: block.timestamp,
            numSubmissions: sentimentScores[tokenAddress].numSubmissions + 1
        });
        
        // Store in history
        historicalData[tokenAddress].push(sentimentScores[tokenAddress]);
        
        // Update node stats
        oracleNodes[msg.sender].totalSubmissions++;
        oracleNodes[msg.sender].lastSubmissionTime = block.timestamp;
        
        emit SentimentUpdated(tokenAddress, score, confidence, block.timestamp);
    }
    
    // ============================================
    // Admin Functions - Node Management
    // ============================================
    
    /**
     * @notice Authorize an oracle node
     * @param nodeAddress Address of the oracle node
     * @param nodeName Name of the oracle node
     */
    function authorizeNode(address nodeAddress, string memory nodeName)
        external
        onlyOwner
    {
        require(nodeAddress != address(0), "Invalid address");
        
        authorizedNodes[nodeAddress] = true;
        oracleNodes[nodeAddress] = OracleNode({
            nodeAddress: nodeAddress,
            nodeName: nodeName,
            isActive: true,
            totalSubmissions: 0,
            lastSubmissionTime: 0
        });
        
        emit NodeAuthorized(nodeAddress, nodeName);
    }
    
    /**
     * @notice Revoke an oracle node
     * @param nodeAddress Address of the oracle node
     */
    function revokeNode(address nodeAddress) external onlyOwner {
        authorizedNodes[nodeAddress] = false;
        oracleNodes[nodeAddress].isActive = false;
        emit NodeRevoked(nodeAddress);
    }
    
    // ============================================
    // Admin Functions - Token Management
    // ============================================
    
    /**
     * @notice Add a supported token
     * @param tokenAddress Address of the token
     */
    function addToken(address tokenAddress) external onlyOwner {
        require(tokenAddress != address(0), "Invalid address");
        require(!isSupportedToken[tokenAddress], "Token already supported");
        
        isSupportedToken[tokenAddress] = true;
        supportedTokens.push(tokenAddress);
        
        emit TokenAdded(tokenAddress);
    }
    
    /**
     * @notice Remove a supported token
     * @param tokenAddress Address of the token
     */
    function removeToken(address tokenAddress) external onlyOwner {
        require(isSupportedToken[tokenAddress], "Token not supported");
        
        isSupportedToken[tokenAddress] = false;
        
        // Remove from array
        for (uint256 i = 0; i < supportedTokens.length; i++) {
            if (supportedTokens[i] == tokenAddress) {
                supportedTokens[i] = supportedTokens[supportedTokens.length - 1];
                supportedTokens.pop();
                break;
            }
        }
        
        emit TokenRemoved(tokenAddress);
    }
    
    /**
     * @notice Update the update frequency
     * @param newFrequency New frequency in seconds
     */
    function setUpdateFrequency(uint256 newFrequency) external onlyOwner {
        require(newFrequency > 0, "Invalid frequency");
        updateFrequency = newFrequency;
    }
    
    /**
     * @notice Transfer ownership
     * @param newOwner Address of the new owner
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
    }
    
    // ============================================
    // View Functions - Statistics
    // ============================================
    
    /**
     * @notice Get oracle node information
     * @param nodeAddress Address of the oracle node
     * @return Node information
     */
    function getNodeInfo(address nodeAddress)
        external
        view
        returns (OracleNode memory)
    {
        return oracleNodes[nodeAddress];
    }
    
    /**
     * @notice Get number of supported tokens
     * @return Number of supported tokens
     */
    function getSupportedTokenCount() external view returns (uint256) {
        return supportedTokens.length;
    }
    
    /**
     * @notice Check if a token is supported
     * @param tokenAddress Address of the token
     * @return True if token is supported
     */
    function isTokenSupported(address tokenAddress) external view returns (bool) {
        return isSupportedToken[tokenAddress];
    }
}
