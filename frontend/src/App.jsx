import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./context/AuthContext"
import Landing from "./pages/Landing"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import CreateBrand from "./pages/CreateBrand"
import EditBrand from "./pages/EditBrand"
import BrandChat from "./pages/BrandChat"
import StorylineReview from "./pages/StorylineReview"
import VideoProgress from "./pages/VideoProgress"
import VideoPlayer from "./pages/VideoPlayer"
import CampaignsList from "./pages/CampaignsList"
import Editor from "./pages/Editor"

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return user ? children : <Navigate to="/login" />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
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
        path="/editor"
        element={
          <PrivateRoute>
            <Editor />
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
        path="/brands/:brandId/edit"
        element={
          <PrivateRoute>
            <EditBrand />
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
