# Product Requirements Document: Hockey Pickup Game Manager

## Introduction/Overview

The Hockey Pickup Game Manager is a web-based application designed to streamline the organization and management of pickup hockey games. The platform solves the critical problem of ensuring adequate player attendance for games by providing automated invitation systems, availability tracking, and intelligent spare player management. 

Built as a multi-tenant SaaS application, it allows multiple hockey teams/groups to independently manage their pickup games without seeing each other's data. The application features bilingual support (English/French) and is designed with future expansion to other sports in mind.

## Goals

1. **Ensure Game Viability**: Guarantee sufficient player attendance for each scheduled pickup game through automated invitation and tracking systems
2. **Streamline Communication**: Eliminate manual coordination by automating player invitations and availability confirmations via email
3. **Intelligent Backup Management**: Automatically invite appropriate spare players when regulars decline, using position-based matching and fair rotation
4. **Comprehensive Game Tracking**: Provide tools to record and display game statistics and player assignments
5. **Multi-Tenant Scalability**: Support dozens of independent teams/groups with complete data isolation
6. **Accessibility**: Deliver a bilingual (English/French) user experience accessible across desktop and mobile devices

## User Stories

### Admin/Organizer Stories
- As a game organizer, I want to create a roster of regular and spare players so that I have a pool of people to invite to games
- As a game organizer, I want to schedule pickup games using a calendar interface so that I can plan games efficiently
- As a game organizer, I want to automatically send email invitations to regular players so that I don't have to manually contact everyone
- As a game organizer, I want to see real-time availability responses so that I can quickly assess if a game will have enough players
- As a game organizer, I want the system to automatically invite spare players when regulars decline so that games remain viable without manual intervention
- As a game organizer, I want to record game statistics so that players can track their performance over time
- As a game organizer, I want to assign tasks to players (like bringing equipment) so that game logistics are managed

### Player Stories
- As a player, I want to receive email invitations for games so that I know when I'm needed
- As a player, I want to easily confirm my availability via email or web link so that the organizer knows my status
- As a player, I want to view my game statistics so that I can track my performance
- As a spare player, I want to be notified when regular players can't make it so that I have opportunities to play

## Functional Requirements

### 1. Multi-Tenant Architecture
1.1. The system must support multiple independent teams/organizations with complete data isolation
1.2. Each tenant must have their own subdomain or unique URL path
1.3. Users must only see data belonging to their organization
1.4. The system must support tenant-specific branding and configuration

### 2. User Management & Authentication
2.1. The system must support multiple admin users per tenant with identical permissions
2.2. Admins must be able to manually add all players to the system
2.3. The system must store player information including name, email, position, and player type (regular/spare), as well as allow them to upload their photo.
2.4. The system must support three position types: Goaltender, Defence, Forward
2.5. The system must categorize players as "Regular" or "Spare"
2.6. The system must allow editing and deleting of players.

### 3. Game Scheduling
3.1 Because 2 teams are playing against each other, the admin should define the team names and jersey colors for each team before scheduling games. 
3.2. Admins must be able to schedule pickup games using a calendar interface
3.3. The system must support both one-time games and recurring game templates
3.4. Game scheduling must include date, time, venue, and required player counts per position
3.5. The system must allow editing and cancellation of scheduled games

### 4. Invitation & Availability System
4.1. The system must automatically send email invitations to all regular players for scheduled games
4.2. Players must be able to respond "Yes" or "No" via email reply or web link
4.3. The system must provide a dashboard showing real-time availability responses for each game
4.4. Email invitations must be available in both English and French based on player preference

### 5. Spare Player Management
5.1. When a regular player declines, the system must automatically invite an appropriate spare player for that position
5.2 The system should allow the admin to implement 2 tiers of spare players:
   - Priority 1: These players are invited first when a regular player declines
   - Priority 2: These players are invited second when a regular player declines
5.3. The system must implement a fair rotation algorithm to cycle through available spare players in the Priority 1 tier. Only when all Priority 1 spares are invited should the system invite Priority 2 spares.
5.4. Spare invitations must respect position requirements (goaltender replaced by goaltender, etc.). There should be a preference for admins to select the positions when the system is setup - selecting one of the following options:
   - Goaltender, Defence and Forwards
   OR
   - Goaltender, and Skaters
The second option just lumps Defence and Forwards together.
5.5. The system must track spare player invitation history to ensure fair distribution

### 6. Game Statistics Tracking
6.1. The system must allow recording of goals with scorer and assist information
6.2. The system must track goal timing including period and time within period
6.3. The system must support penalty tracking including player, penalty type, and duration
6.4. Statistics must be viewable by game and aggregated by player over time
6.5. The system must generate basic reports and summaries of player performance
6.6 The system must allow recording of player attendance for each game - which can generate statistics syucjh as goals per game, assists per game, etc.
6.7 The system should record which goaltender played for which team - this can be used to generate goaltender statistics automatically, such as shutouts, goals allowed, goals against average, and wins/losses.

### 7. Assignment Management
7.1. Admins must be able to assign tasks to players for specific games (e.g., "bring pucks", "bring beer")
7.2. The system must track assignment completion status
7.3. Players must be notified of their assignments via email
7.4. The system must display assignments on the game details page
7.5. The system must allow editing and cancellation of assignments
7.6 The system should have a setting for admins to allow them to decide if they want to manually give assignments to players for each game,  or if the system should automatically give asssignments to regular players on a rotating basis - which should also take into account their availability (they should not have an assignment if they cannot play).

### 8. Internationalization
8.1. The entire user interface must be available in English and French
8.2. Users must be able to select their preferred language
8.3. Email communications must be sent in the recipient's preferred language
8.4. The system must support easy addition of new languages in the future

### 9. Responsive Design
9.1. The application must be desktop-first with full mobile responsiveness
9.2. All core functionality must be accessible on mobile devices
9.3. The interface must be optimized for common screen sizes (desktop, tablet, mobile)

## Non-Goals (Out of Scope)

- Payment processing and fee collection (future requirement)
- League game management and tournament brackets (future expansion)
- Player skill ratings or matchmaking algorithms to create lineups for each team for each game (future expansion)
- Advanced statistics beyond goals, assists, and penalties
- Native mobile applications (web-responsive only)
- Integration with external calendar systems (Google Calendar, Outlook)
- Real-time chat or messaging between players
- Social media integration
- Player skill ratings or matchmaking algorithms
- Equipment management or inventory tracking

## Design Considerations

### User Interface
- Clean, modern design following current web standards
- Intuitive navigation suitable for users of varying technical skill levels
- Clear visual indicators for game status (confirmed, at-risk, cancelled)
- Dashboard-style layout for admins with key metrics prominently displayed
- Mobile-first responsive design patterns

### Email Templates
- Professional, branded email templates for invitations
- Clear call-to-action buttons for availability responses
- Bilingual template support with automatic language selection
- Plain text fallbacks for email clients that don't support HTML

## Technical Considerations

### Frontend Technology Stack
- **Framework**: React.js with modern hooks and functional components
- **Styling**: CSS-in-JS or Tailwind CSS for responsive design
- **State Management**: Context API or Redux for complex state
- **Routing**: React Router for single-page application navigation
- **Internationalization**: react-i18next for bilingual support

### Backend Technology Stack
- **Framework**: Flask (Python) with Blueprint architecture for modularity
- **Database**: PostgreSQL with proper indexing for multi-tenant queries
- **ORM**: SQLAlchemy for database interactions
- **Authentication**: Flask-Login with session management
- **Email**: Flask-Mail with SMTP configuration for transactional emails

### Database Design
- Multi-tenant architecture with tenant_id foreign keys on all relevant tables
- Proper indexing on tenant_id and frequently queried fields
- Separate tables for: tenants, users, players, games, invitations, responses, statistics, assignments
- Audit trails for key actions (invitations sent, responses received)

### Security & Performance
- Input validation and sanitization on all user inputs
- SQL injection prevention through parameterized queries
- Rate limiting on email sending to prevent abuse
- Database connection pooling for performance
- Caching strategies for frequently accessed data

## Success Metrics

### Primary Metrics
- **Game Completion Rate**: 95% of scheduled games have sufficient players to proceed
- **Response Rate**: 80% of invited players respond within 24 hours
- **Spare Utilization**: Fair distribution of spare player invitations (no spare gets >50% more invitations than others)

### Secondary Metrics
- **User Adoption**: 90% of team members actively use the system within 30 days
- **Email Engagement**: 70% email open rate, 60% click-through rate on invitations
- **Mobile Usage**: 40% of interactions occur on mobile devices
- **Language Distribution**: Track usage patterns between English and French interfaces

### Technical Metrics
- **System Uptime**: 99.5% availability
- **Response Time**: Page loads under 2 seconds on average
- **Email Delivery**: 98% successful email delivery rate

## Open Questions

1. **Email Service Provider**: Which email service should be used for transactional emails? (SendGrid, Mailgun, AWS SES)
2. **Tenant Onboarding**: What is the process for new teams to sign up and configure their tenant?
3. **Data Retention**: How long should historical game data and statistics be retained?
4. **Backup Strategy**: What are the requirements for data backup and disaster recovery?
5. **Integration Points**: Are there any existing systems (websites, databases) that need integration?
6. **Notification Preferences**: Should players be able to customize their notification preferences beyond language?
7. **Game Capacity**: What are the expected limits for concurrent games, players per tenant, and total system load?
8. **Admin Hierarchy**: Should there be any distinction between different admin roles in the future?

## Implementation Phases

### Phase 1: Core MVP (Months 1-2)
- Multi-tenant user authentication and basic player management
- Game scheduling with calendar interface
- Email invitation system with basic templates
- Simple availability tracking dashboard

### Phase 2: Automation & Intelligence (Months 3-4)
- Automated spare player invitation system with rotation logic
- Bilingual support implementation
- Enhanced email templates and response handling
- Mobile responsive design optimization

### Phase 3: Statistics & Assignments (Months 5-6)
- Game statistics recording and reporting
- Assignment management system
- Performance analytics and reporting
- System optimization and testing

### Phase 4: Polish & Scale (Month 7+)
- Advanced reporting and analytics
- Performance optimization for scale
- Enhanced user experience features
- Preparation for league game expansion
