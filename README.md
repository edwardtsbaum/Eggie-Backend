# Secure User System API

A privacy-focused user authentication system built with FastAPI, Motor, and MongoDB. This system ensures that users cannot see each other's existence and maintains the highest level of privacy.

## Features

- **Secure Authentication**: JWT-based authentication with bcrypt password hashing
- **Privacy-First Design**: Users cannot see other users' existence
- **Activity Tracking**: Private activity logging for each user
- **Account Management**: User registration, login, profile management, and account deletion
- **Security Features**: IP tracking, user agent logging, automatic data cleanup

## Security Considerations

### Privacy Protection
- No user enumeration endpoints
- No public user lists or search functionality
- All queries are scoped to the authenticated user
- Sensitive data is never exposed in responses

### Data Security
- Passwords are hashed using bcrypt
- JWT tokens with configurable expiration
- IP address and user agent tracking for security
- Automatic cleanup of old activity data

## Setup Instructions

### 1. Install Dependencies

```bash
pipenv install
```

### 2. Environment Configuration

Copy `config.env.example` to `.env` and configure:

```bash
# MongoDB Configuration
MONGO_USERNAME=your_mongo_username
MONGO_PASSWORD=your_mongo_password
MONGO_HOST=your_mongo_host

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=True
ENVIRONMENT=development
```

**Important**: Generate a strong SECRET_KEY for production:
```python
import secrets
secrets.token_urlsafe(32)
```

### 3. Database Setup

Ensure your MongoDB instance is running and accessible. The system will automatically create the necessary collections:
- `users` - User accounts and authentication data
- `user_activities` - Private activity logs for each user

### 4. Run the Application

```bash
pipenv run python main.py
```

Or with uvicorn directly:
```bash
pipenv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token
- `GET /auth/me` - Get current user profile
- `POST /auth/logout` - Logout (client-side token discard)
- `DELETE /auth/account` - Delete user account

### Activities
- `GET /activities/` - Get user's activities
- `GET /activities/count` - Get activity count
- `POST /activities/` - Create new activity
- `DELETE /activities/` - Delete all user activities

## Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Access Protected Endpoints
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Create Activity
```bash
curl -X POST "http://localhost:8000/activities/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "login",
    "description": "User logged in successfully",
    "metadata": {"ip": "192.168.1.1"}
  }'
```

## Privacy Features

1. **No User Enumeration**: The API doesn't provide endpoints to list users or check if emails exist
2. **Scoped Queries**: All database queries are scoped to the authenticated user
3. **Minimal Response Data**: Only necessary data is returned in responses
4. **Automatic Cleanup**: Old activity data is automatically deleted
5. **Secure Headers**: No sensitive information in response headers

## Production Considerations

1. **Environment Variables**: Use strong, unique SECRET_KEY
2. **HTTPS**: Always use HTTPS in production
3. **Rate Limiting**: Implement rate limiting for authentication endpoints
4. **Monitoring**: Set up monitoring for suspicious activity patterns
5. **Backup**: Regular database backups with encryption
6. **Logging**: Implement secure logging without sensitive data

## Development

### Project Structure
```
backend/
├── database/
│   ├── mongo.py          # MongoDB connection
│   ├── user_db.py        # User database operations
│   └── activity_db.py    # Activity database operations
├── models/
│   ├── user.py           # User Pydantic models
│   └── activity.py       # Activity Pydantic models
├── utils/
│   └── security.py       # Security utilities
├── dependencies/
│   └── auth.py           # Authentication dependencies
├── endpoints/
│   ├── auth.py           # Authentication endpoints
│   └── activities.py     # Activity endpoints
├── main.py               # FastAPI application
└── Pipfile               # Dependencies
```

## License

This project is designed for educational and development purposes. Ensure compliance with relevant privacy laws and regulations in your jurisdiction. 