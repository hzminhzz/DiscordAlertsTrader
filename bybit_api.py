"""
Bybit API Client for DiscordAlertsTrader
Supports crypto trading via Bybit's V5 API
"""

from pybit.unified_trading import HTTP
import logging
from typing import Dict, List, Optional, Union
import time

logger = logging.getLogger(__name__)


class BybitClient:
    """
    Bybit API client for executing crypto trades
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Initialize Bybit client
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet environment (default: False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize Bybit HTTP session
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        
        logger.info(f"Bybit client initialized (Testnet: {testnet})")
    
    def get_account_info(self) -> Dict:
        """
        Get account information
        
        Returns:
            Dict containing account information
        """
        try:
            response = self.session.get_wallet_balance(
                accountType="UNIFIED"
            )
            return response
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self, category: str = "linear") -> List[Dict]:
        """
        Get current positions
        
        Args:
            category: Product type (linear, inverse, spot)
            
        Returns:
            List of position dictionaries
        """
        try:
            response = self.session.get_positions(
                category=category,
                settleCoin="USDT"
            )
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        category: str = "linear",
        time_in_force: str = "GTC"
    ) -> Dict:
        """
        Place an order on Bybit
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "Buy" or "Sell"
            order_type: "Market" or "Limit"
            qty: Order quantity
            price: Limit price (required for Limit orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            category: Product type (linear, inverse, spot)
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Dict containing order response
        """
        try:
            order_params = {
                "category": category,
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(qty),
                "timeInForce": time_in_force
            }
            
            # Add price for limit orders
            if order_type == "Limit" and price:
                order_params["price"] = str(price)
            
            # Add stop loss and take profit if provided
            if stop_loss:
                order_params["stopLoss"] = str(stop_loss)
            if take_profit:
                order_params["takeProfit"] = str(take_profit)
            
            response = self.session.place_order(**order_params)
            logger.info(f"Order placed: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e)}
    
    def close_position(
        self,
        symbol: str,
        category: str = "linear"
    ) -> Dict:
        """
        Close an existing position
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            category: Product type
            
        Returns:
            Dict containing close response
        """
        try:
            # Get current position
            positions = self.get_positions(category=category)
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not position or float(position.get('size', 0)) == 0:
                logger.warning(f"No open position found for {symbol}")
                return {"error": "No open position"}
            
            # Determine side to close (opposite of current position)
            side = "Sell" if position['side'] == "Buy" else "Buy"
            qty = abs(float(position['size']))
            
            # Place market order to close
            return self.place_order(
                symbol=symbol,
                side=side,
                order_type="Market",
                qty=qty,
                category=category
            )
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {"error": str(e)}
    
    def cancel_order(self, order_id: str, symbol: str, category: str = "linear") -> Dict:
        """
        Cancel an existing order
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair
            category: Product type
            
        Returns:
            Dict containing cancel response
        """
        try:
            response = self.session.cancel_order(
                category=category,
                symbol=symbol,
                orderId=order_id
            )
            logger.info(f"Order cancelled: {response}")
            return response
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {"error": str(e)}
    
    def get_ticker_price(self, symbol: str, category: str = "linear") -> Optional[float]:
        """
        Get current ticker price
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            category: Product type
            
        Returns:
            Current price or None
        """
        try:
            response = self.session.get_tickers(
                category=category,
                symbol=symbol
            )
            ticker = response.get('result', {}).get('list', [])
            if ticker:
                return float(ticker[0].get('lastPrice', 0))
            return None
        except Exception as e:
            logger.error(f"Error getting ticker price: {e}")
            return None
    
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        category: str = "linear",
        limit: int = 50
    ) -> List[Dict]:
        """
        Get order history
        
        Args:
            symbol: Trading pair (optional)
            category: Product type
            limit: Number of records to return
            
        Returns:
            List of order dictionaries
        """
        try:
            params = {
                "category": category,
                "limit": limit
            }
            if symbol:
                params["symbol"] = symbol
                
            response = self.session.get_order_history(**params)
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            return []
    
    def set_leverage(self, symbol: str, buy_leverage: int, sell_leverage: int, category: str = "linear") -> Dict:
        """
        Set leverage for a symbol
        
        Args:
            symbol: Trading pair
            buy_leverage: Leverage for long positions
            sell_leverage: Leverage for short positions
            category: Product type
            
        Returns:
            Dict containing response
        """
        try:
            response = self.session.set_leverage(
                category=category,
                symbol=symbol,
                buyLeverage=str(buy_leverage),
                sellLeverage=str(sell_leverage)
            )
            logger.info(f"Leverage set for {symbol}: {response}")
            return response
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            return {"error": str(e)}


# Helper function to parse Discord alerts for crypto symbols
def parse_crypto_symbol(alert_text: str) -> Optional[str]:
    """
    Parse crypto symbol from Discord alert
    
    Args:
        alert_text: Discord alert message
        
    Returns:
        Formatted symbol for Bybit (e.g., "BTCUSDT")
    """
    import re
    
    # Common crypto patterns
    patterns = [
        r'\b(BTC|ETH|SOL|DOGE|XRP|ADA|MATIC|AVAX|DOT|LINK)[/\-]?USDT?\b',
        r'\b(BTC|ETH|SOL|DOGE|XRP|ADA|MATIC|AVAX|DOT|LINK)\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, alert_text, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            return f"{symbol}USDT"
    
    return None
