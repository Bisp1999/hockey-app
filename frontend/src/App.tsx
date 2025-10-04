import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { TenantProvider } from './contexts/TenantContext';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import Dashboard from './components/Dashboard/Dashboard';
import PlayerList from './components/Players/PlayerList';
import GameList from './components/Games/GameList';
import InvitationDashboard from './components/Invitations/InvitationDashboard';
import StatsDashboard from './components/Statistics/StatsDashboard';
import AssignmentManager from './components/Assignments/AssignmentManager';
import TeamSettings from './components/Teams/TeamSettings';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import PlayerProfile from './components/Players/PlayerProfile';
import GamesContainer from './components/Games/GamesContainer';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <TenantProvider>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="players" element={<PlayerList />} />
                <Route path="players/:id" element={<PlayerProfile />} />  
                <Route path="invitations" element={<InvitationDashboard />} />
                <Route path="statistics" element={<StatsDashboard />} />
                <Route path="assignments" element={<AssignmentManager />} />
                <Route path="games" element={<GamesContainer />} />
                <Route path="teams" element={<TeamSettings />} />
              </Route>
            </Routes>
          </div>
        </TenantProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
