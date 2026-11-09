import { createBrowserRouter } from 'react-router-dom'
import RequireAuth from './auth/RequireAuth'
import AppLayout from './components/layout/AppLayout'
import AddItemPage from './pages/AddItemPage'
import ClosetPage from './pages/ClosetPage'
import ContextPage from './pages/ContextPage'
import GuidePage from './pages/GuidePage'
import LoginPage from './pages/LoginPage'
import MyPage from './pages/MyPage'
import NotFoundPage from './pages/NotFoundPage'
import SignupPage from './pages/SignupPage'
import TodayPage from './pages/TodayPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <TodayPage /> },
          { path: '/context', element: <ContextPage /> },
          { path: '/guide/:outfitId', element: <GuidePage /> },
          { path: '/closet', element: <ClosetPage /> },
          { path: '/closet/new', element: <AddItemPage /> },
          { path: '/my', element: <MyPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
])
