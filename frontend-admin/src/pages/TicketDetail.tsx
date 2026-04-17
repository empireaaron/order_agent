import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Tag, Descriptions, Timeline, Button, Input, Space, message as antdMessage } from 'antd'
import api from '../services/api'
import { getPriorityColor, getStatusColor } from '../utils/formatters'

interface Ticket {
  id: string
  ticket_no: string
  title: string
  content: string
  priority: string
  category: string
  status: string
  customer_id: string
  customer_info?: Record<string, string>
  created_at: string
  updated_at: string
}

interface TicketMessage {
  id: string
  ticket_id: string
  sender_id: string
  sender_type: string
  content: string
  message_type: string
  is_read: boolean
  created_at: string
}

const TicketDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [messages, setMessages] = useState<TicketMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [replyLoading, setReplyLoading] = useState(false)

  const fetchTicket = async () => {
    if (!id) return
    setLoading(true)
    try {
      const response = await api.get(`/tickets/${id}`)
      setTicket(response.data)
    } catch (error) {
      console.error('Failed to fetch ticket:', error)
      antdMessage.error('获取工单详情失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchMessages = async () => {
    if (!id) return
    try {
      const response = await api.get(`/tickets/${id}/messages`)
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to fetch messages:', error)
      antdMessage.error('获取消息记录失败')
    }
  }

  useEffect(() => {
    fetchTicket()
    fetchMessages()
  }, [id])

  const handleSendMessage = async () => {
    if (!message.trim() || !id) return
    setReplyLoading(true)
    try {
      await api.post(`/tickets/${id}/messages`, {
        content: message,
        sender_type: 'customer',
      })
      setMessage('')
      fetchMessages()  // 刷新消息列表
    } catch (error) {
      console.error('Failed to send message:', error)
      antdMessage.error('发送回复失败')
    } finally {
      setReplyLoading(false)
    }
  }

  if (!ticket) {
    return <Card loading={loading}>加载中...</Card>
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>工单详情</h1>

      <Card title="基本信息" style={{ marginBottom: 24 }}>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="工单编号">{ticket.ticket_no}</Descriptions.Item>
          <Descriptions.Item label="标题">{ticket.title}</Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag color={getPriorityColor(ticket.priority)}>
              {ticket.priority.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={getStatusColor(ticket.status)}>
              {ticket.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="分类">{ticket.category}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{ticket.created_at}</Descriptions.Item>
          <Descriptions.Item label="内容" span={2}>
            {ticket.content}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="处理记录">
        <Timeline
          items={[
            {
              children: `工单创建 - ${ticket.created_at}`,
            },
            {
              children: '等待处理',
            },
          ]}
        />
      </Card>

      <Card title={`消息记录 (${messages.length})`} style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                justifyContent: msg.sender_type === 'agent' ? 'flex-end' : 'flex-start',
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  maxWidth: '70%',
                  padding: '12px 16px',
                  borderRadius: 8,
                  backgroundColor: msg.sender_type === 'agent' ? '#1890ff' : '#f0f0f0',
                  color: msg.sender_type === 'agent' ? '#fff' : '#000',
                }}
              >
                <div style={{ fontSize: 12, marginBottom: 4, opacity: 0.8 }}>
                  {msg.sender_type === 'agent' ? '客服' : msg.sender_type === 'customer' ? '客户' : '系统'}
                  {' · '}
                  {new Date(msg.created_at).toLocaleString()}
                </div>
                <div>{msg.content}</div>
              </div>
            </div>
          ))}
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#999', padding: '20px 0' }}>
              暂无消息
            </div>
          )}
        </Space>
      </Card>

      <Card title="回复" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input.TextArea
            rows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="输入回复内容..."
          />
          <Button type="primary" onClick={handleSendMessage} loading={replyLoading}>
            发送回复
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default TicketDetailPage