import React, { useState, useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Space, Badge } from 'antd'
import {
  DashboardOutlined,
  MessageOutlined,
  BookOutlined,
  UserOutlined,
  LogoutOutlined,
  CustomerServiceOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../services/api'

const { Header, Sider, Content } = Layout

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [pendingCount, setPendingCount] = useState(0)

  // 获取待处理工单数量（未分配的open状态工单）
  useEffect(() => {
    const fetchPendingCount = async () => {
      if (user?.role?.code !== 'admin' && user?.role?.code !== 'agent') {
        return
      }
      try {
        const response = await api.get('/tickets/admin/all?status=open&limit=100')
        // 过滤未分配的工单
        const unassignedCount = response.data.filter((t: any) => !t.assigned_agent_id).length
        setPendingCount(unassignedCount)
      } catch (error) {
        console.error('Failed to fetch pending count:', error)
      }
    }

    fetchPendingCount()
    // 每30秒刷新一次
    const interval = setInterval(fetchPendingCount, 30000)
    return () => clearInterval(interval)
  }, [user])

  // 根据角色动态生成菜单
  const getMenuItems = () => {
    const items = [
      {
        key: '/',
        icon: <DashboardOutlined />,
        label: '仪表盘',
      },
      {
        key: '/tickets',
        icon: <MessageOutlined />,
        label: '我的工单',
      },
    ]

    // 只有客服/管理员显示工单处理中心和客服工作台
    if (user?.role?.code === 'admin' || user?.role?.code === 'agent') {
      items.push({
        key: '/admin/tickets',
        icon: <CustomerServiceOutlined />,
        label: (
          <Space>
            工单处理中心
            {pendingCount > 0 && <Badge count={pendingCount} size="small" />}
          </Space>
        ),
      },
      {
        key: '/chat-workplace',
        icon: <MessageOutlined />,
        label: '客服工作台',
      })
    }

    items.push(
      {
        key: '/knowledge',
        icon: <BookOutlined />,
        label: '知识库',
      },
      {
        key: '/users',
        icon: <UserOutlined />,
        label: '用户管理',
      }
    )

    // 只有管理员显示系统监控
    if (user?.role?.code === 'admin') {
      items.push({
        key: '/metrics',
        icon: <LineChartOutlined />,
        label: '系统监控',
      })
    }

    return items
  }

  const handleMenuClick = (key: string) => {
    navigate(key)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="light"
        breakpoint="lg"
        collapsedWidth="0"
        style={{
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
        }}
      >
        <div
          style={{
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <h2 style={{ margin: 0, color: '#1890ff' }}>TicketBot</h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          style={{ borderRight: 0 }}
          items={getMenuItems().map((item) => ({
            key: item.key,
            icon: item.icon,
            label: item.label,
            onClick: () => handleMenuClick(item.key),
          }))}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <div />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.full_name || user?.username}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: '24px',
            padding: '24px',
            background: '#fff',
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout