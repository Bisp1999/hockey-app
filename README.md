# Hockey Pickup Manager

A multi-tenant web application for managing hockey pickup games, built with React frontend and Flask backend.

## Features

- **Multi-tenant Architecture**: Support for multiple independent teams/organizations
- **Player Management**: Manage regular and spare players with priority tiers
- **Game Scheduling**: Calendar-based scheduling with recurring game templates
- **Automated Invitations**: Email invitations with availability tracking
- **Smart Spare Management**: Intelligent spare player rotation system
- **Statistics Tracking**: Comprehensive game and player statistics
- **Assignment Management**: Task assignment for game logistics
- **Bilingual Support**: Full English and French localization
- **Responsive Design**: Mobile-optimized interface

## Tech Stack

### Backend
- **Flask**: Python web framework
- **PostgreSQL**: Database with multi-tenant architecture
- **SQLAlchemy**: ORM for database operations
- **Flask-Mail**: Email integration
- **Flask-Login**: Authentication system

### Frontend
- **React**: JavaScript UI framework
- **TypeScript**: Type-safe development
- **React Router**: Client-side routing
- **React i18next**: Internationalization
- **Axios**: HTTP client

### Development
- **Docker Compose**: Containerized development environment
- **MailHog**: Email testing
- **Redis**: Session storage (optional)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hockey-app
   ```

2. **Build and start services**
   ```bash
   make build
   make up
   ```
   
   Or without Make:
   ```bash
   docker-compose build
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

3. **Initialize the database**
   ```bash
   make db-init
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - MailHog (email testing): http://localhost:8025

### Available Commands

```bash
make help           # Show all available commands
make up             # Start development environment
make down           # Stop all services
make logs           # Show logs from all services
make shell-backend  # Open shell in backend container
make shell-frontend # Open shell in frontend container
make test           # Run tests
make clean          # Clean up containers and volumes
```

## Project Structure

```
hockey-app/
├── backend/
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── utils/           # Utility functions
│   ├── migrations/      # Database migrations
│   └── templates/       # Email templates
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── contexts/    # React contexts
│   │   ├── hooks/       # Custom hooks
│   │   ├── utils/       # Utility functions
│   │   ├── types/       # TypeScript definitions
│   │   └── locales/     # Translation files
│   └── public/
├── docker-compose.yml   # Docker services
└── Makefile            # Development commands
```

## Environment Configuration

Copy `.env.example` to `.env` and update with your configuration:

```bash
cp .env.example .env
```

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask secret key
- `MAIL_SERVER`: SMTP server configuration
- `TENANT_URL_*`: Multi-tenant routing options

## Database

The application uses PostgreSQL with a multi-tenant architecture. All data is isolated by tenant_id to ensure complete separation between organizations.

### Key Models
- **Tenant**: Organization/team configuration
- **User**: Admin users with tenant association
- **Player**: Players with positions and spare priorities
- **Game**: Scheduled games with team assignments
- **Invitation**: Game invitations and responses
- **Statistics**: Game and player performance data
- **Assignment**: Task assignments for games

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Current user info

### Players
- `GET /api/players` - List players
- `POST /api/players` - Create player
- `PUT /api/players/{id}` - Update player
- `DELETE /api/players/{id}` - Delete player

### Games
- `GET /api/games` - List games
- `POST /api/games` - Create game
- `PUT /api/games/{id}` - Update game
- `DELETE /api/games/{id}` - Delete game

### Invitations
- `POST /api/invitations` - Send invitations
- `POST /api/invitations/{id}/respond` - Respond to invitation
- `GET /api/invitations/game/{id}` - Game invitations

## Testing

Run the test suite:
```bash
make test
```

Or individually:
```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test
```

## Deployment

For production deployment:

1. Update environment variables for production
2. Use production Docker Compose configuration
3. Set up SSL certificates
4. Configure production email service
5. Set up database backups

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license information here]
