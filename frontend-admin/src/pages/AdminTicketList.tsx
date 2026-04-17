import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table, Tag, Button, Space, Card, Select, message,
  Tabs, Badge, Modal, Input, Descriptions, Divider, Avatar
} from 'antd'
import {
  EyeOutlined, UserOutlined, CheckCircleOutlined,
  ClockCircleOutlined, ExclamationCircleOutlined
} from '@ant-design/icons'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'
import { getPriorityColor } from '../utils/formatters'

interface Ticket {
  id: string
  ticket_no: string
  title: string
  content: string
  priority: string
  category: string
  status: string
  customer_id: string
  assigned_agent_id: string | null
  customer_info: {
    username: string
    email: string
    phone: string
  }
  created_at: string
  updated_at: string
}

interface TicketMessage {
  id: string
  sender_type: string
  content: string
  created_at: string
}

const AdminTicketListPage: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [allTickets, setAllTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('open')
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [replyContent, setReplyContent] = useState('')
  const [messages, setMessages] = useState<TicketMessage[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)

  const fetchTickets = async (status?: string) => {
    setLoading(true)
    try {
      let url = '/tickets/admin/all?limit=100'
      if (status && status !== 'all') {
        url += `&status=${status}`
      }
      const response = await api.get(url)
      setTickets(response.data)
    } catch (error) {
      message.error('获取工单列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取所有工单用于统计数量
  const fetchAllTickets = async () => {
    try {
      const response = await api.get('/tickets/admin/all?limit=1000')
      setAllTickets(response.data)
    } catch (error) {
      console.error('Failed to fetch all tickets:', error)
      message.error('获取全部工单失败')
    }
  }

  useEffect(() => {
    fetchTickets(activeTab === 'all' ? undefined : activeTab)
  }, [activeTab])

  useEffect(() => {
    fetchAllTickets()
    // 每30秒刷新一次统计数据
    const interval = setInterval(fetchAllTickets, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleAssign = async (ticketId: string) => {
    try {
      await api.patch(`/tickets/${ticketId}/assign`)
      message.success('工单已分配给您')
      fetchTickets(activeTab === 'all' ? undefined : activeTab)
      fetchAllTickets()
    } catch (error) {
      message.error('分配工单失败')
    }
  }

  const handleStatusChange = async (ticketId: string, newStatus: string) => {
    try {
      await api.patch(`/tickets/${ticketId}/status`, {
        to_status: newStatus,
        note: `状态变更为 ${newStatus}`
      })
      message.success('状态更新成功')
      fetchTickets(activeTab === 'all' ? undefined : activeTab)
      fetchAllTickets()
      if (selectedTicket) {
        setSelectedTicket({ ...selectedTicket, status: newStatus })
      }
    } catch (error) {
      message.error('状态更新失败')
    }
  }

  const fetchMessages = async (ticketId: string) => {
    setMessagesLoading(true)
    try {
      const response = await api.get(`/tickets/${ticketId}/messages`)
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to fetch messages:', error)
      message.error('获取消息记录失败')
    } finally {
      setMessagesLoading(false)
    }
  }

  const handleReply = async () => {
    if (!selectedTicket || !replyContent.trim()) return
    try {
      await api.post(`/tickets/${selectedTicket.id}/messages`, {
        content: replyContent,
        sender_type: 'agent'
      })
      message.success('回复发送成功')
      setReplyContent('')
      // 刷新消息列表
      fetchMessages(selectedTicket.id)
    } catch (error) {
      message.error('发送回复失败')
    }
  }

  const getStatusTag = (status: string) => {
    const config: Record<string, { color: string; text: string }> = {
      open: { color: 'blue', text: '待处理' },
      pending: { color: 'orange', text: '待回复' },
      in_progress: { color: 'cyan', text: '处理中' },
      resolved: { color: 'green', text: '已解决' },
      closed: { color: 'default', text: '已关闭' }
    }
    const { color, text } = config[status] || { color: 'default', text: status }
    return <Tag color={color}>{text}</Tag>
  }

  const getPriorityTag = (priority: string) => {
    const config: Record<string, { color: string; text: string }> = {
      low: { color: 'green', text: '低' },
      normal: { color: 'blue', text: '普通' },
      high: { color: 'orange', text: '高' },
      urgent: { color: 'red', text: '紧急' }
    }
    const { color, text } = config[priority] || { color: 'default', text: priority }
    return <Tag color={color}>{text}</Tag>
  }

  const columns = [
    {
      title: '工单编号',
      dataIndex: 'ticket_no',
      key: 'ticket_no',
      width: 160,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => getPriorityTag(priority)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '客户',
      key: 'customer',
      width: 150,
      render: (record: Ticket) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          <span>{record.customer_info?.username || '未知'}</span>
        </Space>
      )
    },
    {
      title: '分配给',
      key: 'assigned',
      width: 150,
      render: (record: Ticket) => (
        record.assigned_agent_id ? (
          <Tag color="blue">已分配</Tag>
        ) : (
          <Tag color="orange">未分配</Tag>
        )
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (record: Ticket) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedTicket(record)
              setIsModalVisible(true)
              fetchMessages(record.id)
            }}
          >
            处理
          </Button>
          {!record.assigned_agent_id && (
            <Button
              size="small"
              onClick={() => handleAssign(record.id)}
            >
              接单
            </Button>
          )}
        </Space>
      )
    }
  ]

  // 统计数量（使用所有工单数据，不受当前筛选影响）
  const getStatusCount = (status: string) => {
    return allTickets.filter(t => t.status === status).length
  }

  const tabItems = [
    { key: 'open', label: `待处理 (${getStatusCount('open')})` },
    { key: 'in_progress', label: `处理中 (${getStatusCount('in_progress')})` },
    { key: 'pending', label: `待回复 (${getStatusCount('pending')})` },
    { key: 'resolved', label: `已解决 (${getStatusCount('resolved')})` },
    { key: 'all', label: '全部' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>工单处理中心</h1>
        <div>
          <span style={{ marginRight: 16 }}>
            当前客服: <strong>{user?.username}</strong>
          </span>
        </div>
      </div>

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={columns}
          dataSource={tickets}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 工单详情弹窗 */}
      <Modal
        title="工单详情"
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false)
          setSelectedTicket(null)
          setReplyContent('')
          setMessages([])
        }}
        width={800}
        footer={null}
      >
        {selectedTicket && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="工单编号">{selectedTicket.ticket_no}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(selectedTicket.status)}</Descriptions.Item>
              <Descriptions.Item label="优先级">{getPriorityTag(selectedTicket.priority)}</Descriptions.Item>
              <Descriptions.Item label="分类">{selectedTicket.category}</Descriptions.Item>
              <Descriptions.Item label="客户">{selectedTicket.customer_info?.username}</Descriptions.Item>
              <Descriptions.Item label="联系">{selectedTicket.customer_info?.email || selectedTicket.customer_info?.phone}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{selectedTicket.created_at}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{selectedTicket.updated_at}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <div style={{ marginBottom: 16 }}>
              <h4>问题描述</h4>
              <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                <strong>{selectedTicket.title}</strong>
                <p style={{ marginTop: 8 }}>{selectedTicket.content}</p>
              </div>
            </div>

            <Divider />

            {/* 消息历史 */}
            <div style={{ marginBottom: 16 }}>
              <h4>消息记录 ({messages.length})</h4>
              <div style={{ maxHeight: 300, overflow: 'auto', background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                {messagesLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px 0' }}>加载中...</div>
                ) : messages.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>暂无消息</div>
                ) : (
                  messages.map((msg) => (
                    <div key={msg.id} style={{ marginBottom: 12 }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: msg.sender_type === 'agent' ? 'flex-end' : 'flex-start'
                      }}>
                        <div style={{
                          maxWidth: '80%',
                          padding: '8px 12px',
                          borderRadius: 8,
                          backgroundColor: msg.sender_type === 'agent' ? '#1890ff' : '#fff',
                          color: msg.sender_type === 'agent' ? '#fff' : '#000',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}>
                          <div style={{ fontSize: 12, marginBottom: 4, opacity: 0.8 }}>
                            {msg.sender_type === 'agent' ? '客服' : msg.sender_type === 'customer' ? '客户' : '系统'}
                            {' · '}
                            {new Date(msg.created_at).toLocaleString()}
                          </div>
                          <div>{msg.content}</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <Divider />

            <div style={{ marginBottom: 16 }}>
              <h4>状态操作</h4>
              <Space>
                {selectedTicket.status !== 'in_progress' && (
                  <Button
                    type="primary"
                    onClick={() => handleStatusChange(selectedTicket.id, 'in_progress')}
                  >
                    开始处理
                  </Button>
                )}
                {selectedTicket.status !== 'pending' && (
                  <Button
                    onClick={() => handleStatusChange(selectedTicket.id, 'pending')}
                  >
                    标记待回复
                  </Button>
                )}
                {selectedTicket.status !== 'resolved' && (
                  <Button
                    type="primary"
                    ghost
                    onClick={() => handleStatusChange(selectedTicket.id, 'resolved')}
                  >
                    标记已解决
                  </Button>
                )}
                {selectedTicket.status !== 'closed' && (
                  <Button
                    danger
                    onClick={() => handleStatusChange(selectedTicket.id, 'closed')}
                  >
                    关闭工单
                  </Button>
                )}
              </Space>
            </div>

            <Divider />

            <div>
              <h4>回复客户</h4>
              <Input.TextArea
                rows={4}
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="输入回复内容..."
                style={{ marginBottom: 8 }}
              />
              <Button type="primary" onClick={handleReply} disabled={!replyContent.trim()}>
                发送回复
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default AdminTicketListPage