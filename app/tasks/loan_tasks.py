from app import create_app
from app.services.loan_service import LoanService
import time
import threading

def check_overdue_loans():
    """Check for overdue loans and update their status."""
    app = create_app()
    with app.app_context():
        loan_service = LoanService()
        overdue_count = loan_service.check_overdue_loans()
        print(f"Checked for overdue loans: {overdue_count} found")

def start_loan_scheduler():
    """Start a scheduler to run loan-related tasks periodically."""
    def run_scheduler():
        while True:
            # Check for overdue loans every hour
            check_overdue_loans()
            
            # Sleep for an hour
            time.sleep(3600)
    
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Loan scheduler started")