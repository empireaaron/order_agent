import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme as antdTheme } from 'antd'
import zhCN from 'antd/locale/zh_CN'

import { useAuthStore } from './stores/authStore'
import MainLayout from './layouts/MainLayout'
import LoginPage from './pages/Login'
import DashboardPage from './pages/Dashboard'
import TicketListPage from './pages/TicketList'
import TicketDetailPage from './pages/TicketDetail'
import AdminTicketListPage from './pages/AdminTicketList'
import KnowledgeBasePage from './pages/KnowledgeBase'
import KnowledgeBaseDetailPage from './pages/KnowledgeBaseDetail'
import UsersPage from './pages/Users'
import ChatWorkplace from './pages/ChatWorkplace'
import MetricsPage from './pages/Metrics'
import SamplingAnnotationPage from './pages/SamplingAnnotation'

function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
        />
        <Route
          path="/"
          element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" replace />}
        >
          <Route index element={<DashboardPage />} />
          <Route path="tickets" element={<TicketListPage />} />
          <Route path="tickets/:id" element={<TicketDetailPage />} />
          <Route path="admin/tickets" element={<AdminTicketListPage />} />
          <Route path="knowledge" element={<KnowledgeBasePage />} />
          <Route path="knowledge/:id" element={<KnowledgeBaseDetailPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="chat-workplace" element={<ChatWorkplace />} />
          <Route path="metrics" element={<MetricsPage />} />
          <Route path="sampling-annotation" element={<SamplingAnnotationPage />} />
        </Route>
      </Routes>
    </ConfigProvider>
  )
}

export default App