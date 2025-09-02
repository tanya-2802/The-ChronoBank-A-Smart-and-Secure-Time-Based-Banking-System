from app import create_app
from app.services.investment_service import InvestmentService
import time
import threading

def check_matured_investments():
    """Check for matured investments and update their status."""
    app = create_app()
    with app.app_context():
        investment_service = InvestmentService()
        matured_count = investment_service.check_matured_investments()
        print(f"Checked for matured investments: {matured_count} found")

def start_investment_scheduler():
    """Start a scheduler to run investment-related tasks periodically."""
    def run_scheduler():
        while True:
            # Check for matured investments every hour
            check_matured_investments()
            
            # Sleep for an hour
            time.sleep(3600)
    
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Investment scheduler started")