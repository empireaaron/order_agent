import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, List, Tag, Badge, Skeleton } from 'antd'
import {
  MessageOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TeamOutlined,
  CustomerServiceOutlined,
} from '@ant-design/icons'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts'
import api from '../services/api'
import dayjs from 'dayjs'

// 统计数据类型
interface DashboardStats {
  tickets: {
    pending: number
    today: number
    today_resolved: number
    total_resolved: number
  }
  agents: {
    online: number
  }
  sessions: {
    active: number
    waiting: number
  }
}

// 趋势数据类型
interface TicketTrends {
  dates: string[]
  created: number[]
  resolved: number[]
}

// 分类数据类型
interface CategoryStat {
  category: string
  name: string
  count: number
}

// 活动类型
interface Activity {
  type: string
  ticket_id: string
  ticket_no: string
  title: string
  customer: string
  priority: string
  status: string
  created_at: string
}

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [trends, setTrends] = useState<TicketTrends | null>(null)
  const [categories, setCategories] = useState<CategoryStat[]>([])
  const [activities, setActivities] = useState<Activity[]>([])

  // 优先级颜色映射
  const priorityColors: Record<string, string> = {
    low: 'blue',
    normal: 'green',
    high: 'orange',
    urgent: 'red',
  }

  const priorityLabels: Record<string, string> = {
    low: '低',
    normal: '普通',
    high: '高',
    urgent: '紧急',
  }

  // 状态颜色映射
  const statusColors: Record<string, string> = {
    open: 'blue',
    pending: 'orange',
    in_progress: 'processing',
    resolved: 'green',
    closed: 'default',
  }

  const statusLabels: Record<string, string> = {
    open: '待处理',
    pending: '待回复',
    in_progress: '处理中',
    resolved: '已解决',
    closed: '已关闭',
  }

  // 分类颜色
  const categoryColors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1']

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // 并行获取所有数据
      const [statsRes, trendsRes, categoriesRes, activitiesRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/ticket-trends?days=7'),
        api.get('/dashboard/ticket-categories'),
        api.get('/dashboard/recent-activities?limit=10'),
      ])

      setStats(statsRes.data)
      setTrends(trendsRes.data)
      setCategories(categoriesRes.data)
      setActivities(activitiesRes.data)
    } catch (error) {
      console.error('获取仪表盘数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 转换趋势数据为图表格式
  const trendChartData = trends
    ? trends.dates.map((date, index) => ({
        date,
        创建: trends.created[index],
        解决: trends.resolved[index],
      }))
    : []

  // 转换分类数据为图表格式
  const categoryChartData = categories.map((cat) => ({
    name: cat.name,
    value: cat.count,
  }))

  return (
    <div>
      <h1 style={{ marginBottom: '24px' }}>仪表盘</h1>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待处理工单"
              value={stats?.tickets.pending || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日工单"
              value={stats?.tickets.today || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日解决"
              value={stats?.tickets.today_resolved || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="在线客服"
              value={stats?.agents.online || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#722ed1' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* 会话统计 */}
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="进行中会话"
              value={stats?.sessions.active || 0}
              prefix={<CustomerServiceOutlined />}
              valueStyle={{ color: '#13c2c2' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="等待中会话"
              value={stats?.sessions.waiting || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#eb2f96' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        {/* 工单趋势图 */}
        <Col xs={24} lg={12}>
          <Card title="工单趋势（最近7天）">
            {loading ? (
              <Skeleton active paragraph={{ rows: 6 }} />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="创建"
                    stroke="#1890ff"
                    strokeWidth={2}
                    dot={{ fill: '#1890ff' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="解决"
                    stroke="#52c41a"
                    strokeWidth={2}
                    dot={{ fill: '#52c41a' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>

        {/* 工单分类饼图 */}
        <Col xs={24} lg={12}>
          <Card title="工单分类统计">
            {loading ? (
              <Skeleton active paragraph={{ rows: 6 }} />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={categoryColors[index % categoryColors.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
      </Row>

      {/* 最近活动 */}
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        <Col xs={24}>
          <Card title="最近活动">
            {loading ? (
              <Skeleton active paragraph={{ rows: 5 }} />
            ) : (
              <List
                dataSource={activities}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>{item.title}</span>
                          <Tag color={priorityColors[item.priority]}>
                            {priorityLabels[item.priority]}
                          </Tag>
                          <Badge
                            status={statusColors[item.status] as any}
                            text={statusLabels[item.status]}
                          />
                        </div>
                      }
                      description={
                        <div>
                          <span>工单号: {item.ticket_no}</span>
                          <span style={{ marginLeft: '16px' }}>
                            客户: {item.customer}
                          </span>
                          <span style={{ marginLeft: '16px', color: '#999' }}>
                            {dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
                          </span>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage