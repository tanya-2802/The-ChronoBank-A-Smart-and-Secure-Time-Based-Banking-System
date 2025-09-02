from app import create_app
from app.tasks.loan_tasks import start_loan_scheduler
from app.tasks.investment_tasks import start_investment_scheduler

app = create_app()

if __name__ == '__main__':
    # Start the loan scheduler in a background thread
    start_loan_scheduler()
    
    # Start the investment scheduler in a background thread
    start_investment_scheduler()
    
    # Run the Flask application
    app.run(debug=True)
