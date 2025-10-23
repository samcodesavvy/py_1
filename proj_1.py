from __future__ import annotations
from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
import datetime
from functools import total_ordering

# --- Added Missing Classes ---

class IncompatibleCurrencyError(ValueError):
    """Raised when an operation is attempted on two different currencies."""
    pass

@total_ordering
class AdvancedMoney:
    """
    A class to represent a monetary value with a specific currency.
    Handles currency-safe arithmetic and comparisons.
    """
    def __init__(self, amount: str | Decimal | int, currency: str = 'USD'):
        # Quantize to 2 decimal places, standard for most currencies
        self.amount = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.currency = currency.upper()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.amount}', '{self.currency}')"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    def _check_currency(self, other: AdvancedMoney) -> None:
        if not isinstance(other, AdvancedMoney):
            raise TypeError(f"Cannot operate on AdvancedMoney and {type(other)}")
        if self.currency != other.currency:
            raise IncompatibleCurrencyError(
                f"Currency mismatch: {self.currency} and {other.currency}"
            )

    def __add__(self, other: AdvancedMoney) -> AdvancedMoney:
        self._check_currency(other)
        return AdvancedMoney(self.amount + other.amount, self.currency)

    def __sub__(self, other: AdvancedMoney) -> AdvancedMoney:
        self._check_currency(other)
        return AdvancedMoney(self.amount - other.amount, self.currency)

    def __mul__(self, other: int | Decimal | float) -> AdvancedMoney:
        if not isinstance(other, (int, Decimal, float)):
            return NotImplemented
        return AdvancedMoney(self.amount * Decimal(other), self.currency)

    def __rmul__(self, other: int | Decimal | float) -> AdvancedMoney:
        return self.__mul__(other)
        
    def __truediv__(self, other: int | Decimal | float) -> AdvancedMoney:
        if not isinstance(other, (int, Decimal, float)):
            return NotImplemented
        if other == 0:
            raise ZeroDivisionError("Cannot divide money by zero")
        return AdvancedMoney(self.amount / Decimal(other), self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AdvancedMoney):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __gt__(self, other: AdvancedMoney) -> bool:
        self._check_currency(other)
        return self.amount > other.amount
        
# --- Your Original Code (Rewritten and Fixed) ---

class PaymentMethod(ABC):
    """Abstract base class for payment methods"""
    
    @abstractmethod
    def process_payment(self, amount: AdvancedMoney) -> bool:
        """Process a payment"""
        pass
    
    @abstractmethod
    def get_fees(self, amount: AdvancedMoney) -> AdvancedMoney:
        """Calculate processing fees"""
        pass

class CreditCardPayment(PaymentMethod):
    """Credit card payment processing"""
    
    def __init__(self, fee_rate: Decimal = Decimal('0.029')):  # 2.9% fee
        self.fee_rate = fee_rate
    
    def process_payment(self, amount: AdvancedMoney) -> bool:
        """Process credit card payment"""
        print(f"Processing credit card payment of {amount}")
        return True
    
    def get_fees(self, amount: AdvancedMoney) -> AdvancedMoney:
        """Calculate credit card processing fee"""
        fee_amount = amount * self.fee_rate
        return AdvancedMoney(fee_amount.amount, amount.currency)

class BankTransferPayment(PaymentMethod):
    """Bank transfer payment processing"""
    
    def __init__(self, flat_fee: AdvancedMoney = None):
        self.flat_fee = flat_fee or AdvancedMoney('2.50', 'USD')
    
    def process_payment(self, amount: AdvancedMoney) -> bool:
        """Process bank transfer"""
        print(f"Processing bank transfer of {amount}")
        return True
    
    def get_fees(self, amount: AdvancedMoney) -> AdvancedMoney:
        """Calculate bank transfer fee"""
        if amount.currency != self.flat_fee.currency:
            raise IncompatibleCurrencyError("Currency mismatch for fee calculation")
        return self.flat_fee

class AccountBalance(AdvancedMoney):
    """Money subclass for account balances with transaction history"""
    
    def __init__(self, amount, currency='USD', account_type='checking'):
        super().__init__(amount, currency)
        self.account_type = account_type
        self.transactions: list[dict] = []
        self.created_date = datetime.datetime.now()
    
    def _copy_state_to(self, new_instance: AccountBalance):
        """Helper to copy state for the immutable pattern."""
        new_instance.transactions = self.transactions.copy()
        new_instance.created_date = self.created_date
    
    def deposit(self, amount: AdvancedMoney, description: str = "Deposit") -> AccountBalance:
        """Make a deposit"""
        if amount.currency != self.currency:
            raise IncompatibleCurrencyError(f"Cannot deposit {amount.currency} to {self.currency}")
        
        # **FIX:** Use `self.__class__` to create an instance of the
        # correct subclass (e.g., AccountBalance or InvestmentBalance)
        new_balance = self.__class__(
            self.amount + amount.amount, 
            self.currency, 
            self.account_type
        )
        # **FIX:** Copy state to the new instance
        self._copy_state_to(new_balance)
        
        new_balance.transactions.append({
            'type': 'deposit',
            'amount': amount,
            'description': description,
            'timestamp': datetime.datetime.now(),
            'balance_after': new_balance
        })
        return new_balance
    
    def withdraw(self, amount: AdvancedMoney, description: str = "Withdrawal") -> AccountBalance:
        """Make a withdrawal"""
        if amount.currency != self.currency:
            raise IncompatibleCurrencyError(f"Cannot withdraw {amount.currency} from {self.currency}")
        
        if amount > self: # `self` works as AdvancedMoney
            raise ValueError("Insufficient funds")
        
        # **FIX:** Use `self.__class__`
        new_balance = self.__class__(
            self.amount - amount.amount, 
            self.currency, 
            self.account_type
        )
        # **FIX:** Copy state to the new instance
        self._copy_state_to(new_balance)
        
        new_balance.transactions.append({
            'type': 'withdrawal',
            'amount': amount,
            'description': description,
            'timestamp': datetime.datetime.now(),
            'balance_after': new_balance
        })
        return new_balance
    
    def transfer_to(self, target_account: AccountBalance, amount: AdvancedMoney, 
                    description: str = "Transfer") -> tuple[AccountBalance, AccountBalance]:
        """Transfer money to another account"""
        if amount.currency != self.currency or amount.currency != target_account.currency:
            raise IncompatibleCurrencyError("Currency mismatch for transfer")
        
        # Withdraw from source
        new_source_balance = self.withdraw(amount, f"Transfer to {target_account.account_type}")
        
        # Deposit to target
        new_target_balance = target_account.deposit(amount, f"Transfer from {self.account_type}")
        
        return new_source_balance, new_target_balance
    
    def get_transaction_history(self, limit: int = 10) -> list[dict]:
        """Get recent transaction history"""
        return self.transactions[-limit:]
    
    def calculate_interest(self, annual_rate: Decimal, days: int = 30) -> AdvancedMoney:
        """Calculate interest for account (savings accounts)"""
        if self.account_type not in ['savings', 'money_market']:
            return AdvancedMoney('0', self.currency)
        
        daily_rate = annual_rate / Decimal('365')
        interest_amount = self.amount * daily_rate * Decimal(days)
        return AdvancedMoney(interest_amount, self.currency)

class InvestmentBalance(AccountBalance):
    """Specialized balance for investment accounts"""
    
    def __init__(self, amount, currency='USD'):
        super().__init__(amount, currency, 'investment')
        self.holdings: dict[str, int] = {}  # symbol -> quantity
        self.cost_basis: dict[str, AdvancedMoney] = {}  # symbol -> average cost
    
    def _copy_state_to(self, new_instance: AccountBalance):
        """Copy base state and investment-specific state."""
        super()._copy_state_to(new_instance)
        if isinstance(new_instance, InvestmentBalance):
            new_instance.holdings = self.holdings.copy()
            new_instance.cost_basis = self.cost_basis.copy()
    
    def buy_stock(self, symbol: str, quantity: int, price_per_share: AdvancedMoney) -> InvestmentBalance:
        """Buy stock"""
        total_cost = price_per_share * quantity
        
        if total_cost > self:
            raise ValueError("Insufficient funds for purchase")
        
        # **FIX:** `self.withdraw` now correctly returns an `InvestmentBalance`
        # We type-cast here to help static analysis, though it's guaranteed
        new_balance = self.withdraw(total_cost, f"Buy {quantity} shares of {symbol}")
        assert isinstance(new_balance, InvestmentBalance)

        # Update holdings
        if symbol in new_balance.holdings:
            old_quantity = new_balance.holdings[symbol]
            old_cost_basis = new_balance.cost_basis[symbol]
            
            # Calculate new average cost
            total_shares = old_quantity + quantity
            total_cost_basis = (old_quantity * old_cost_basis) + total_cost
            new_cost_basis = total_cost_basis / total_shares
            
            new_balance.holdings[symbol] = total_shares
            new_balance.cost_basis[symbol] = new_cost_basis
        else:
            new_balance.holdings[symbol] = quantity
            new_balance.cost_basis[symbol] = price_per_share
        
        return new_balance
    
    def sell_stock(self, symbol: str, quantity: int, price_per_share: AdvancedMoney) -> InvestmentBalance:
        """Sell stock"""
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError(f"Insufficient shares of {symbol}")
        
        total_proceeds = price_per_share * quantity
        
        # **FIX:** `self.deposit` now correctly returns an `InvestmentBalance`
        new_balance = self.deposit(total_proceeds, f"Sell {quantity} shares of {symbol}")
        assert isinstance(new_balance, InvestmentBalance)

        # Update holdings
        new_balance.holdings[symbol] -= quantity
        if new_balance.holdings[symbol] == 0:
            del new_balance.holdings[symbol]
            del new_balance.cost_basis[symbol]
        
        # Calculate gain/loss
        original_cost = self.cost_basis[symbol] * quantity
        # **FIX:** Corrected calculation (was `AdvancedMoney(original_cost.amount, ...)`
        gain_loss = total_proceeds - original_cost
        
        new_balance.transactions[-1]['gain_loss'] = gain_loss
        
        return new_balance
    
    def get_portfolio_value(self, current_prices: dict[str, AdvancedMoney]) -> AdvancedMoney:
        """Calculate total portfolio value"""
        # **FIX:** This was an indentation error
        cash_value = AdvancedMoney(self.amount, self.currency)
        stock_value = AdvancedMoney('0', self.currency)
        
        for symbol, quantity in self.holdings.items():
            if symbol in current_prices:
                stock_value += current_prices[symbol] * quantity
        
        return cash_value + stock_value

# --- Demonstration Code ---

if __name__ == "__main__":
    
    print("=== Money Inheritance Hierarchy ===")
    # Create accounts
    checking = AccountBalance('1000.00', 'USD', 'checking')
    savings = AccountBalance('5000.00', 'USD', 'savings')
    investment = InvestmentBalance('10000.00', 'USD')
    
    print(f"Initial balances:")
    print(f"Checking: {checking}")
    print(f"Savings: {savings}")
    print(f"Investment: {investment}")
    
    # Account operations
    deposit_amount = AdvancedMoney('500.00', 'USD')
    checking = checking.deposit(deposit_amount, "Payroll deposit")
    print(f"\nAfter deposit: {checking}")
    
    # Transfer between accounts
    transfer_amount = AdvancedMoney('200.00', 'USD')
    checking, savings = checking.transfer_to(savings, transfer_amount, "Emergency fund")
    print(f"After transfer - Checking: {checking}, Savings: {savings}")
    
    # Investment operations
    apple_price = AdvancedMoney('150.00', 'USD')
    investment = investment.buy_stock('AAPL', 10, apple_price)
    print(f"\nAfter buying AAPL: {investment}")
    print(f"Holdings: {investment.holdings}")
    print(f"Cost basis: {investment.cost_basis}")

    # Sell some stock
    new_apple_price = AdvancedMoney('160.00', 'USD')
    investment = investment.sell_stock('AAPL', 5, new_apple_price)
    print(f"\nAfter selling 5 AAPL: {investment}")
    print(f"Remaining holdings: {investment.holdings}")
    print(f"Remaining cost basis: {investment.cost_basis}")

    # Check transaction history
    print(f"\nRecent transactions for {investment.account_type}:")
    for i, transaction in enumerate(investment.get_transaction_history(3), 1):
        # **FIX:** Corrected cut-off f-string
        print(f"{i}. {transaction['type'].title()}: {transaction['amount']} - {transaction['description']}")
        if 'gain_loss' in transaction:
            print(f"   Gain/Loss: {transaction['gain_loss']}")
    
    # Payment processing demonstration
    print(f"\n=== Payment Processing ===")
    payment_amount = AdvancedMoney('100.00', 'USD')
    
    # Credit card payment
    cc_processor = CreditCardPayment()
    cc_fee = cc_processor.get_fees(payment_amount)
    print(f"Credit card payment of {payment_amount}")
    print(f"Processing fee: {cc_fee}")
    print(f"Total charge: {payment_amount + cc_fee}")
    
    # Bank transfer payment
    bt_processor = BankTransferPayment()
    bt_fee = bt_processor.get_fees(payment_amount)
    print(f"\nBank transfer payment of {payment_amount}")
    print(f"Processing fee: {bt_fee}")
    print(f"Total charge: {payment_amount + bt_fee}")
    
    # Interest calculation
    annual_rate = Decimal('0.02')  # 2% APY
    interest = savings.calculate_interest(annual_rate, 30)
    print(f"\nSavings account interest (2% APY, 30 days): {interest}")
    
    # Portfolio valuation
    current_prices = {'AAPL': AdvancedMoney('165.00', 'USD')}
    portfolio_value = investment.get_portfolio_value(current_prices)
    print(f"Total portfolio value: {portfolio_value}")