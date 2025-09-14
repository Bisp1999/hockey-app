# Development Tasks: Hockey Pickup Game Manager

Based on the PRD analysis, this is a greenfield project requiring full-stack development with React frontend, Flask backend, PostgreSQL database, and multi-tenant architecture.

## Relevant Files

### Backend Files
- `app.py` - Main Flask application entry point with multi-tenant configuration
- `config.py` - Application configuration including database and email settings
- `requirements.txt` - Python dependencies for Flask, SQLAlchemy, Flask-Mail, etc.
- `models/__init__.py` - Database models initialization
- `models/tenant.py` - Tenant model for multi-tenant architecture
- `models/user.py` - User and admin models with authentication
- `models/player.py` - Player model with positions, types, and photo upload
- `models/team.py` - Team model with names and jersey colors
- `models/game.py` - Game scheduling and management models
- `models/invitation.py` - Invitation and availability response models
- `models/statistics.py` - Game statistics and attendance tracking models
- `models/assignment.py` - Assignment management models
- `routes/auth.py` - Authentication and tenant management routes
- `routes/players.py` - Player management API endpoints
- `routes/games.py` - Game scheduling and management API endpoints
- `routes/invitations.py` - Invitation and availability API endpoints
- `routes/statistics.py` - Statistics tracking API endpoints
- `routes/assignments.py` - Assignment management API endpoints
- `utils/email.py` - Email service utilities for invitations
- `utils/spare_rotation.py` - Spare player rotation algorithm
- `utils/tenant.py` - Multi-tenant utility functions
- `migrations/` - Database migration scripts

### Frontend Files
- `package.json` - React dependencies and build scripts
- `src/App.js` - Main React application with routing
- `src/index.js` - React application entry point
- `src/contexts/AuthContext.js` - Authentication context provider
- `src/contexts/TenantContext.js` - Multi-tenant context provider
- `src/components/Layout/Header.js` - Main navigation header
- `src/components/Layout/Sidebar.js` - Navigation sidebar
- `src/components/Auth/Login.js` - Login component
- `src/components/Players/PlayerList.js` - Player management interface
- `src/components/Players/PlayerForm.js` - Add/edit player form
- `src/components/Teams/TeamConfig.js` - Team configuration interface
- `src/components/Games/GameCalendar.js` - Game scheduling calendar
- `src/components/Games/GameForm.js` - Game creation/editing form
- `src/components/Games/GameDetails.js` - Game details and availability view
- `src/components/Invitations/InvitationDashboard.js` - Availability tracking dashboard
- `src/components/Statistics/StatsDashboard.js` - Game statistics interface
- `src/components/Statistics/StatsEntry.js` - Statistics entry form
- `src/components/Assignments/AssignmentManager.js` - Assignment management interface
- `src/utils/api.js` - API client utilities
- `src/utils/constants.js` - Application constants
- `src/locales/en.json` - English translations
- `src/locales/fr.json` - French translations
- `src/hooks/useAuth.js` - Authentication custom hook
- `src/hooks/useApi.js` - API interaction custom hook

### Configuration Files
- `.env.example` - Environment variables template
- `docker-compose.yml` - Docker configuration for development
- `Dockerfile` - Container configuration
- `nginx.conf` - Nginx configuration for production

### Test Files
- `tests/test_models.py` - Backend model tests
- `tests/test_routes.py` - Backend API endpoint tests
- `tests/test_utils.py` - Backend utility function tests
- `src/components/__tests__/` - Frontend component tests
- `src/utils/__tests__/` - Frontend utility tests

### Notes

- Unit tests should be placed alongside the code files they are testing
- Use `pytest` for backend testing and `Jest` for frontend testing
- Database migrations should be versioned and include both upgrade and downgrade paths
- Email templates should be stored in `templates/email/` directory

## Tasks

- [ ] 1.0 Project Setup and Infrastructure
  - [x] 1.1 Initialize Flask backend project structure with blueprints
  - [x] 1.2 Set up PostgreSQL database with multi-tenant schema design
  - [x] 1.3 Create React frontend project with TypeScript support
  - [x] 1.4 Configure development environment with Docker Compose
  - [x] 1.5 Set up version control with proper .gitignore files
  - [x] 1.6 Create environment configuration files (.env templates)
  - [x] 1.7 Set up basic CI/CD pipeline structure

- [ ] 2.0 Multi-Tenant Architecture and Authentication System
  - [x] 2.1 Design and implement tenant model with subdomain/path routing
  - [x] 2.2 Create user authentication system with Flask-Login
  - [x] 2.3 Implement tenant isolation middleware for all database queries
  - [x] 2.4 Build tenant registration and onboarding flow
  - [ ] 2.5 Create admin user management within tenants
  - [ ] 2.6 Implement session management with tenant context
  - [ ] 2.7 Add security measures (CSRF protection, rate limiting)

- [ ] 3.0 Player Management System
  - [ ] 3.1 Create player model with name, email, position, type, and photo fields
  - [ ] 3.2 Implement player CRUD operations with tenant isolation
  - [ ] 3.3 Build player list interface with search and filtering
  - [ ] 3.4 Create player form with photo upload functionality
  - [ ] 3.5 Implement player type management (Regular/Spare with Priority 1/2)
  - [ ] 3.6 Add position configuration system (3-position vs 2-position modes)
  - [ ] 3.7 Create player profile view with statistics summary

- [ ] 4.0 Team Configuration and Game Scheduling
  - [ ] 4.1 Create team model with names and jersey color configuration
  - [ ] 4.2 Build team setup interface for admins
  - [ ] 4.3 Implement game model with date, time, venue, and player requirements
  - [ ] 4.4 Create calendar-based game scheduling interface
  - [ ] 4.5 Add recurring game template functionality
  - [ ] 4.6 Implement game editing and cancellation features
  - [ ] 4.7 Build game details view with team assignments

- [ ] 5.0 Email Invitation and Availability System
  - [ ] 5.1 Set up Flask-Mail with SMTP configuration
  - [ ] 5.2 Create bilingual email templates for invitations
  - [ ] 5.3 Implement invitation model and tracking system
  - [ ] 5.4 Build automated invitation sending for regular players
  - [ ] 5.5 Create availability response system (email reply + web link)
  - [ ] 5.6 Build real-time availability dashboard for admins
  - [ ] 5.7 Add email preference management for players

- [ ] 6.0 Intelligent Spare Player Management
  - [ ] 6.1 Implement spare player priority system (Priority 1 and 2)
  - [ ] 6.2 Create fair rotation algorithm for spare invitations
  - [ ] 6.3 Build position-based spare matching logic
  - [ ] 6.4 Implement automatic spare invitation triggers
  - [ ] 6.5 Add spare invitation history tracking
  - [ ] 6.6 Create spare player management interface for admins
  - [ ] 6.7 Build notification system for spare opportunities

- [ ] 7.0 Game Statistics and Attendance Tracking
  - [ ] 7.1 Create statistics models for goals, assists, penalties, and attendance
  - [ ] 7.2 Implement game attendance tracking system
  - [ ] 7.3 Build statistics entry interface for post-game data
  - [ ] 7.4 Create goaltender-specific statistics tracking
  - [ ] 7.5 Implement player performance analytics and reports
  - [ ] 7.6 Build statistics dashboard with filtering and sorting
  - [ ] 7.7 Add export functionality for statistics data

- [ ] 8.0 Assignment Management System
  - [ ] 8.1 Create assignment model with task descriptions and player assignments
  - [ ] 8.2 Build manual assignment interface for admins
  - [ ] 8.3 Implement automatic assignment rotation system
  - [ ] 8.4 Add assignment notification system via email
  - [ ] 8.5 Create assignment tracking and completion status
  - [ ] 8.6 Build assignment history and rotation fairness tracking
  - [ ] 8.7 Implement assignment preference settings for tenants

- [ ] 9.0 Internationalization (English/French)
  - [ ] 9.1 Set up React i18next for frontend internationalization
  - [ ] 9.2 Create English and French translation files
  - [ ] 9.3 Implement language selection and persistence
  - [ ] 9.4 Translate all UI components and messages
  - [ ] 9.5 Create bilingual email templates
  - [ ] 9.6 Add backend localization for API responses
  - [ ] 9.7 Test and validate all translations

- [ ] 10.0 Responsive UI and Mobile Optimization
  - [ ] 10.1 Implement responsive design system with CSS Grid/Flexbox
  - [ ] 10.2 Optimize calendar interface for mobile devices
  - [ ] 10.3 Create mobile-friendly forms and input methods
  - [ ] 10.4 Implement touch-friendly navigation and interactions
  - [ ] 10.5 Optimize image upload and display for mobile
  - [ ] 10.6 Test across different screen sizes and devices
  - [ ] 10.7 Implement progressive web app features

- [ ] 11.0 Testing and Quality Assurance
  - [ ] 11.1 Set up pytest for backend testing framework
  - [ ] 11.2 Create unit tests for all models and utilities
  - [ ] 11.3 Implement API endpoint integration tests
  - [ ] 11.4 Set up Jest and React Testing Library for frontend
  - [ ] 11.5 Create component unit tests and integration tests
  - [ ] 11.6 Implement end-to-end testing with Cypress or Playwright
  - [ ] 11.7 Add performance testing and optimization

- [ ] 12.0 Deployment and Production Setup
  - [ ] 12.1 Configure production database with proper indexing
  - [ ] 12.2 Set up production email service (SendGrid/Mailgun)
  - [ ] 12.3 Implement proper logging and monitoring
  - [ ] 12.4 Configure SSL certificates and security headers
  - [ ] 12.5 Set up backup and disaster recovery procedures
  - [ ] 12.6 Create deployment scripts and documentation
  - [ ] 12.7 Perform load testing and performance optimization
