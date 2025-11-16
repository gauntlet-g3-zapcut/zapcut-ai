import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./context/AuthContext"
import Landing from "./pages/Landing"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import CreateBrand from "./pages/CreateBrand"
import BrandChat from "./pages/BrandChat"
import StorylineReview from "./pages/StorylineReview"
import VideoProgress from "./pages/VideoProgress"
import VideoPlayer from "./pages/VideoPlayer"
import Editor from "./pages/Editor"
import CampaignsList from "./pages/CampaignsList"

function PrivateRoute({ children }) {
  // Skip authentication check - always allow access
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/campaigns"
        element={
          <PrivateRoute>
            <CampaignsList />
          </PrivateRoute>
        }
      />
      <Route
        path="/brands/create"
        element={
          <PrivateRoute>
            <CreateBrand />
          </PrivateRoute>
        }
      />
      <Route
        path="/brands/:brandId/chat"
        element={
          <PrivateRoute>
            <BrandChat />
          </PrivateRoute>
        }
      />
      <Route
        path="/brands/:brandId/storyline/:creativeBibleId"
        element={
          <PrivateRoute>
            <StorylineReview />
          </PrivateRoute>
        }
      />
      <Route
        path="/campaigns/:campaignId/progress"
        element={
          <PrivateRoute>
            <VideoProgress />
          </PrivateRoute>
        }
      />
      <Route
        path="/campaigns/:campaignId/video"
        element={
          <PrivateRoute>
            <VideoPlayer />
          </PrivateRoute>
        }
      />
      <Route
        path="/editor"
        element={
          <PrivateRoute>
            <Editor />
          </PrivateRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  )
}

export default App
