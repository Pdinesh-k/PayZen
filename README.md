# PayZen - Smart Bill Payment System

PayZen is a modern, user-friendly bill payment and management system that helps users track, pay, and get reminders for their bills while earning rewards.

## Features

- **User Authentication**
  - Secure registration and login
  - Password protection and session management

- **Bill Management**
  - Add and track bills
  - Set due dates and payment amounts
  - Categorize bills by type
  - Payment processing
  - Bill history tracking

- **Smart Reminders**
  - Automated email reminders for upcoming bills
  - Customizable reminder frequency
  - Due date notifications

- **Rewards System**
  - Earn points for timely payments
  - Redeem points for rewards
  - Track reward history
  - Special bonuses and promotions

- **Responsive Design**
  - Works on desktop and mobile devices
  - Modern, intuitive interface
  - Accessibility features

## Technology Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLAlchemy
- Testing: Pytest, Playwright
- Task Scheduling: APScheduler
- Authentication: JWT

## Prerequisites

- Python 3.8 or higher
- Node.js (for frontend development)
- MySQL/PostgreSQL database

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PayZen.git
cd PayZen
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with the following variables
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_email_password
MAIL_FROM=your_sender_email
MAIL_PORT=587
MAIL_SERVER=your_smtp_server
```

5. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. Access the application:
   - Open your browser and navigate to `http://localhost:8000`
   - Register a new account or login with existing credentials

## Running Tests

1. Install test dependencies:
```bash
pip install pytest pytest-playwright
playwright install
```

2. Run the tests:
```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_api.py
pytest tests/test_ui.py
```

## Project Structure

```
PayZen/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   └── utils.py          # Utility functions
├── static/
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── templates/           # HTML templates
├── tests/
│   ├── test_api.py     # API tests
│   └── test_ui.py      # UI tests
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## API Documentation

- API documentation is available at `/docs` or `/redoc` when the server is running
- Includes all endpoints, request/response schemas, and authentication requirements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
- Open an issue in the GitHub repository
- Contact the development team
- Check the documentation

## Acknowledgments

- Thanks to all contributors
- Built with FastAPI and modern web technologies
- Designed for simplicity and efficiency 