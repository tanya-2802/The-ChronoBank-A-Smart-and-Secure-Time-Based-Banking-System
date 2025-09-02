from abc import ABC, abstractmethod
from datetime import datetime, timedelta

class LoanRepaymentStrategy(ABC):
    """
    Abstract base class for loan repayment strategies.
    
    This class defines the interface for all loan repayment strategies.
    """
    
    @abstractmethod
    def calculate_repayment_amount(self, loan):
        """
        Calculate the total repayment amount for a loan.
        
        Args:
            loan: The loan to calculate the repayment amount for
            
        Returns:
            int: The total repayment amount in seconds
        """
        pass
    
    @abstractmethod
    def calculate_payment_schedule(self, loan):
        """
        Calculate the payment schedule for a loan.
        
        Args:
            loan: The loan to calculate the payment schedule for
            
        Returns:
            list: A list of payment dates and amounts
        """
        pass
    
    @abstractmethod
    def apply_payment(self, loan, payment_amount):
        """
        Apply a payment to a loan.
        
        Args:
            loan: The loan to apply the payment to
            payment_amount: The amount of the payment in seconds
            
        Returns:
            bool: True if the payment was applied successfully, False otherwise
        """
        pass

class FixedRateStrategy(LoanRepaymentStrategy):
    """
    Fixed rate loan repayment strategy.
    
    This strategy applies a fixed interest rate to the loan amount.
    """
    
    def calculate_repayment_amount(self, loan):
        """
        Calculate the total repayment amount for a fixed-rate loan.
        
        Args:
            loan: The loan to calculate the repayment amount for
            
        Returns:
            int: The total repayment amount in seconds
        """
        return int(loan.amount * (1 + loan.interest_rate))
    
    def calculate_payment_schedule(self, loan):
        """
        Calculate the payment schedule for a fixed-rate loan.
        
        Args:
            loan: The loan to calculate the payment schedule for
            
        Returns:
            list: A list of payment dates and amounts
        """
        total_repayment = self.calculate_repayment_amount(loan)
        payment_interval = loan.term_days // 4  # Divide the term into 4 payments
        
        # Ensure payment interval is at least 1 day
        payment_interval = max(payment_interval, 1)
        
        payment_amount = total_repayment // 4  # Equal payments
        final_payment = total_repayment - (payment_amount * 3)  # Adjust final payment for rounding
        
        schedule = []
        for i in range(3):
            payment_date = loan.created_at + timedelta(days=payment_interval * (i + 1))
            schedule.append({
                'date': payment_date,
                'amount': payment_amount
            })
        
        # Add final payment
        schedule.append({
            'date': loan.due_date,
            'amount': final_payment
        })
        
        return schedule
    
    def apply_payment(self, loan, payment_amount):
        """
        Apply a payment to a fixed-rate loan.
        
        Args:
            loan: The loan to apply the payment to
            payment_amount: The amount of the payment in seconds
            
        Returns:
            bool: True if the payment was applied successfully, False otherwise
        """
        return loan.make_payment(payment_amount)

class DynamicRateStrategy(LoanRepaymentStrategy):
    """
    Dynamic rate loan repayment strategy.
    
    This strategy adjusts the interest rate based on market conditions.
    """
    
    def __init__(self, market_rate_adjustment=0.0):
        """
        Initialize the dynamic rate strategy.
        
        Args:
            market_rate_adjustment: The adjustment to apply to the interest rate based on market conditions
        """
        self.market_rate_adjustment = market_rate_adjustment
    
    def calculate_repayment_amount(self, loan):
        """
        Calculate the total repayment amount for a dynamic-rate loan.
        
        Args:
            loan: The loan to calculate the repayment amount for
            
        Returns:
            int: The total repayment amount in seconds
        """
        # Apply market rate adjustment to the interest rate
        effective_rate = loan.interest_rate + self.market_rate_adjustment
        
        # Ensure the effective rate is not negative
        effective_rate = max(effective_rate, 0.01)
        
        return int(loan.amount * (1 + effective_rate))
    
    def calculate_payment_schedule(self, loan):
        """
        Calculate the payment schedule for a dynamic-rate loan.
        
        Args:
            loan: The loan to calculate the payment schedule for
            
        Returns:
            list: A list of payment dates and amounts
        """
        total_repayment = self.calculate_repayment_amount(loan)
        
        # For dynamic loans, we use a graduated payment schedule
        # where payments increase over time
        payment_interval = loan.term_days // 4  # Divide the term into 4 payments
        
        # Ensure payment interval is at least 1 day
        payment_interval = max(payment_interval, 1)
        
        # Calculate graduated payments (increasing over time)
        base_payment = total_repayment // 10
        schedule = []
        
        # First payment: 10% of total
        schedule.append({
            'date': loan.created_at + timedelta(days=payment_interval),
            'amount': base_payment
        })
        
        # Second payment: 20% of total
        schedule.append({
            'date': loan.created_at + timedelta(days=payment_interval * 2),
            'amount': base_payment * 2
        })
        
        # Third payment: 30% of total
        schedule.append({
            'date': loan.created_at + timedelta(days=payment_interval * 3),
            'amount': base_payment * 3
        })
        
        # Final payment: 40% of total (or remaining amount)
        final_payment = total_repayment - (base_payment * 6)
        schedule.append({
            'date': loan.due_date,
            'amount': final_payment
        })
        
        return schedule
    
    def apply_payment(self, loan, payment_amount):
        """
        Apply a payment to a dynamic-rate loan.
        
        Args:
            loan: The loan to apply the payment to
            payment_amount: The amount of the payment in seconds
            
        Returns:
            bool: True if the payment was applied successfully, False otherwise
        """
        # For dynamic loans, we apply a small bonus for early payments
        if datetime.utcnow() < loan.due_date - timedelta(days=loan.term_days // 2):
            # Early payment bonus: 5% more effective payment
            payment_amount = int(payment_amount * 1.05)
        
        return loan.make_payment(payment_amount)

class EarlyRepaymentStrategy(LoanRepaymentStrategy):
    """
    Early repayment loan strategy.
    
    This strategy incentivizes early repayment by offering discounts.
    """
    
    def calculate_repayment_amount(self, loan):
        """
        Calculate the total repayment amount for an early-repayment loan.
        
        Args:
            loan: The loan to calculate the repayment amount for
            
        Returns:
            int: The total repayment amount in seconds
        """
        # Standard calculation initially
        return int(loan.amount * (1 + loan.interest_rate))
    
    def calculate_payment_schedule(self, loan):
        """
        Calculate the payment schedule for an early-repayment loan.
        
        Args:
            loan: The loan to calculate the payment schedule for
            
        Returns:
            list: A list of payment dates and amounts
        """
        total_repayment = self.calculate_repayment_amount(loan)
        
        # For early repayment loans, we suggest a single payment
        # with a discount for early repayment
        schedule = [{
            'date': loan.due_date,
            'amount': total_repayment,
            'note': 'Pay early for a discount!'
        }]
        
        # Add early repayment options with discounts
        early_date_1 = loan.created_at + timedelta(days=loan.term_days // 4)
        early_amount_1 = int(total_repayment * 0.85)  # 15% discount
        
        early_date_2 = loan.created_at + timedelta(days=loan.term_days // 2)
        early_amount_2 = int(total_repayment * 0.9)  # 10% discount
        
        early_date_3 = loan.created_at + timedelta(days=loan.term_days * 3 // 4)
        early_amount_3 = int(total_repayment * 0.95)  # 5% discount
        
        schedule.insert(0, {
            'date': early_date_3,
            'amount': early_amount_3,
            'note': 'Early repayment (5% discount)'
        })
        
        schedule.insert(0, {
            'date': early_date_2,
            'amount': early_amount_2,
            'note': 'Early repayment (10% discount)'
        })
        
        schedule.insert(0, {
            'date': early_date_1,
            'amount': early_amount_1,
            'note': 'Early repayment (15% discount)'
        })
        
        return schedule
    
    def apply_payment(self, loan, payment_amount):
        """
        Apply a payment to an early-repayment loan.
        
        Args:
            loan: The loan to apply the payment to
            payment_amount: The amount of the payment in seconds
            
        Returns:
            bool: True if the payment was applied successfully, False otherwise
        """
        # Calculate discount based on how early the payment is made
        days_remaining = (loan.due_date - datetime.utcnow()).days
        term_fraction = days_remaining / loan.term_days
        
        # Apply discount if paying the full amount
        if payment_amount >= loan.remaining_amount and term_fraction > 0.25:
            if term_fraction >= 0.75:
                # 15% discount if paying in the first quarter of the term
                effective_payment = int(loan.remaining_amount * 0.85)
                loan.remaining_amount = effective_payment
            elif term_fraction >= 0.5:
                # 10% discount if paying in the first half of the term
                effective_payment = int(loan.remaining_amount * 0.9)
                loan.remaining_amount = effective_payment
            elif term_fraction >= 0.25:
                # 5% discount if paying in the first three quarters of the term
                effective_payment = int(loan.remaining_amount * 0.95)
                loan.remaining_amount = effective_payment
        
        return loan.make_payment(payment_amount)

class LoanStrategyFactory:
    """
    Factory for creating loan repayment strategies.
    """
    
    @staticmethod
    def create_strategy(strategy_type, **kwargs):
        """
        Create a loan repayment strategy.
        
        Args:
            strategy_type: The type of strategy to create (FIXED, DYNAMIC, EARLY)
            **kwargs: Additional arguments for the strategy
            
        Returns:
            LoanRepaymentStrategy: The created strategy
        """
        if strategy_type == 'FIXED':
            return FixedRateStrategy()
        elif strategy_type == 'DYNAMIC':
            market_rate_adjustment = kwargs.get('market_rate_adjustment', 0.0)
            return DynamicRateStrategy(market_rate_adjustment)
        elif strategy_type == 'EARLY':
            return EarlyRepaymentStrategy()
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")