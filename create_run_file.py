with open('run.py', 'w') as f:
    f.write('''from app import create_app
from app.tasks.loan_tasks import start_loan_scheduler

app = create_app()

if __name__ == '__main__':
    # Start the loan scheduler in a background thread
    start_loan_scheduler()
    
    # Run the Flask application
    app.run(debug=True)
''')