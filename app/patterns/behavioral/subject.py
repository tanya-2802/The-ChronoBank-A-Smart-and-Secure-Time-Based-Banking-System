from abc import ABC, abstractmethod

class Subject(ABC):
    """
    Subject interface for the Observer pattern.
    
    This interface defines methods for attaching, detaching, and notifying observers.
    """
    
    @abstractmethod
    def attach(self, observer):
        """
        Attach an observer to this subject.
        
        Args:
            observer: The observer to attach
        """
        pass
    
    @abstractmethod
    def detach(self, observer):
        """
        Detach an observer from this subject.
        
        Args:
            observer: The observer to detach
        """
        pass
    
    @abstractmethod
    def notify(self, *args, **kwargs):
        """
        Notify all observers of an event.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        pass

class AccountSubject(Subject):
    """
    Subject implementation for account-related events.
    """
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """
        Attach an observer to this subject.
        
        Args:
            observer: The observer to attach
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        """
        Detach an observer from this subject.
        
        Args:
            observer: The observer to detach
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event_type, *args, **kwargs):
        """
        Notify all observers of an account event.
        
        Args:
            event_type: The type of event (e.g., 'low_balance', 'suspicious_transaction')
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        for observer in self._observers:
            if event_type == 'low_balance':
                observer.on_low_balance(*args, **kwargs)
            elif event_type == 'suspicious_transaction':
                observer.on_suspicious_transaction(*args, **kwargs)
            elif event_type == 'loan_due':
                observer.on_loan_due(*args, **kwargs)

class TransactionSubject(Subject):
    """
    Subject implementation for transaction-related events.
    """
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """
        Attach an observer to this subject.
        
        Args:
            observer: The observer to attach
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        """
        Detach an observer from this subject.
        
        Args:
            observer: The observer to detach
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event_type, *args, **kwargs):
        """
        Notify all observers of a transaction event.
        
        Args:
            event_type: The type of event (e.g., 'transaction_created', 'transaction_completed')
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        for observer in self._observers:
            if event_type == 'transaction_created':
                observer.on_transaction_created(*args, **kwargs)
            elif event_type == 'transaction_completed':
                observer.on_transaction_completed(*args, **kwargs)
            elif event_type == 'transaction_failed':
                observer.on_transaction_failed(*args, **kwargs)