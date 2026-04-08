import React, { useState, useEffect, useRef } from 'react'
import { Card, Badge, Button, List, Avatar, Input, Tag, Empty, Spin } from 'antd'
import { MessageOutlined, UserOutlined, CloseOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../stores/authStore'
import api from '../../services/api'
import './styles.css'

interface ChatSession {
  id: string
  status: 'waiting' | 'connected' | 'closed'
  customer: {
    id: string
    username: string
  }
  agent?: {
    id: string
    name: string
  }
  last_message?: string
  unread_count: number
  created_at: string
}

interface ChatMessage {
  id: string
  content: string
  sender_type: 'customer' | 'agent' | 'system' | 'ai'
  sender?: {
    id: string
    name: string
  } | null
  is_read?: boolean
  created_at: string
}

const ChatWorkplace: React.FC = () => {
  const { user, token } = useAuthStore()
  const [online, setOnline] = useState(false)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [waitingCount, setWaitingCount] = useState(0)
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 建立WebSocket连接
  useEffect(() => {
    if (!online) {
      if (wsRef.current) {
        wsRef.current.close()
      }
      return
    }

    if (!token) return
    const ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Chat WebSocket connected')
      // 获取会话列表
      fetchSessions()
      fetchWaitingQueue()
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    ws.onerror = (error) => {
      console.error('Chat WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('Chat WebSocket closed')
    }

    return () => {
      ws.close()
    }
  }, [online])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'new_message':
        if (data.session_id === activeSession?.id) {
          setMessages(prev => [...prev, data.message])
        } else {
          // 更新未读数
          setSessions(prev => prev.map(s =>
            s.id === data.session_id
              ? { ...s, unread_count: s.unread_count + 1, last_message: data.message.content }
              : s
          ))
        }
        break
      case 'new_waiting_session':
        fetchWaitingQueue()
        break
      case 'session_assigned':
        fetchSessions()
        break
    }
  }

  const fetchSessions = async () => {
    try {
      const response = await api.get('/chat-service/sessions/my?status=connected')
      setSessions(response.data)
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  }

  const fetchWaitingQueue = async () => {
    try {
      const response = await api.get('/chat-service/sessions/waiting')
      setWaitingCount(response.data.length)
    } catch (error) {
      console.error('Failed to fetch waiting queue:', error)
    }
  }

  const goOnline = async () => {
    try {
      await api.post('/chat-service/agent/online')
      setOnline(true)
    } catch (error) {
      console.error('Failed to go online:', error)
    }
  }

  const goOffline = async () => {
    try {
      await api.post('/chat-service/agent/offline')
      setOnline(false)
      setActiveSession(null)
    } catch (error) {
      console.error('Failed to go offline:', error)
    }
  }

  const acceptSession = async (sessionId: string) => {
    try {
      await api.post(`/chat-service/sessions/${sessionId}/accept`)
      // 加入WebSocket会话
      wsRef.current?.send(JSON.stringify({
        type: 'join_session',
        session_id: sessionId,
        role: 'agent'
      }))
      fetchSessions()
      fetchWaitingQueue()
    } catch (error) {
      console.error('Failed to accept session:', error)
    }
  }

  const loadSessionMessages = async (session: ChatSession) => {
    setActiveSession(session)
    setLoading(true)
    try {
      const response = await api.get(`/chat-service/sessions/${session.id}/messages`)
      setMessages(response.data.items || [])
      // 加入WebSocket会话
      wsRef.current?.send(JSON.stringify({
        type: 'join_session',
        session_id: session.id,
        role: 'agent'
      }))
    } catch (error) {
      console.error('Failed to load messages:', error)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = () => {
    if (!inputValue.trim() || !activeSession) return

    wsRef.current?.send(JSON.stringify({
      type: 'chat_message',
      session_id: activeSession.id,
      content: inputValue
    }))

    setInputValue('')
  }

  const closeSession = async () => {
    if (!activeSession) return
    try {
      await api.post(`/chat-service/sessions/${activeSession.id}/close`)
      setActiveSession(null)
      fetchSessions()
    } catch (error) {
      console.error('Failed to close session:', error)
    }
  }

  const formatMessageTime = (createdAt: string) => {
    const date = new Date(createdAt)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    const milliseconds = String(date.getMilliseconds()).padStart(3, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${milliseconds}`
  }

  if (!online) {
    return (
      <div className="chat-offline">
        <Card>
          <Empty
            description="您当前处于离线状态"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={goOnline}>
              上线接单
            </Button>
          </Empty>
        </Card>
      </div>
    )
  }

  return (
    <div className="chat-workplace">
      <div className="chat-sidebar">
        <div className="chat-header">
          <span>会话列表</span>
          <div>
            <Badge count={waitingCount} style={{ marginRight: 16 }}>
              <Button size="small" onClick={fetchWaitingQueue}>
                等待队列
              </Button>
            </Badge>
            <Button size="small" danger onClick={goOffline}>
              下线
            </Button>
          </div>
        </div>

        <List
          dataSource={sessions}
          renderItem={item => (
            <List.Item
              className={`session-item ${activeSession?.id === item.id ? 'active' : ''}`}
              onClick={() => loadSessionMessages(item)}
            >
              <List.Item.Meta
                avatar={<Avatar icon={<UserOutlined />} />}
                title={
                  <span>
                    {item.customer.username}
                    {item.unread_count > 0 && (
                      <Badge count={item.unread_count} style={{ marginLeft: 8 }} />
                    )}
                  </span>
                }
                description={item.last_message?.slice(0, 20) + '...'}
              />
            </List.Item>
          )}
        />
      </div>

      <div className="chat-main">
        {activeSession ? (
          <>
            <div className="chat-main-header">
              <span>{activeSession.customer.username}</span>
              <Button
                size="small"
                danger
                icon={<CloseOutlined />}
                onClick={closeSession}
              >
                结束会话
              </Button>
            </div>

            <div className="chat-messages">
              {loading ? (
                <Spin />
              ) : (
                messages.map(msg => {
                  // 统一渲染规则：
                  // | sender_type | sender_id | 显示名称 |
                  // |-------------|-----------|----------|
                  // | ai          | NULL      | AI助手   |
                  // | customer    | 有值      | 客户     |
                  // | agent       | 有值      | 客服(名) |
                  // | system      | NULL/有值 | 系统     |

                  const getSenderLabel = () => {
                    switch (msg.sender_type) {
                      case 'ai':
                        return 'AI助手';
                      case 'customer':
                        return msg.sender?.name ? `客户(${msg.sender.name})` : '客户';
                      case 'agent':
                        return msg.sender?.name ? `客服(${msg.sender.name})` : '客服';
                      case 'system':
                        return '系统';
                      default:
                        return msg.sender?.name || '系统';
                    }
                  };

                  const isAgent = msg.sender_type === 'agent';

                  return (
                    <div
                      key={msg.id}
                      className={`message ${msg.sender_type}`}
                      style={{
                        display: 'flex',
                        justifyContent: isAgent ? 'flex-end' : 'flex-start',
                        marginBottom: 12
                      }}
                    >
                      {msg.sender_type === 'system' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                          <Tag color="blue">{msg.content}</Tag>
                          <span style={{ fontSize: 11, color: '#999', fontFamily: 'monospace' }}>
                            {formatMessageTime(msg.created_at)}
                          </span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', maxWidth: '70%' }}>
                          {/* 发送者信息在消息框上方 */}
                          <div
                            className="message-header"
                            style={{
                              fontSize: 12,
                              color: '#999',
                              marginBottom: 4,
                              paddingLeft: isAgent ? 0 : 4,
                              paddingRight: isAgent ? 4 : 0,
                              textAlign: isAgent ? 'right' : 'left',
                              whiteSpace: 'nowrap',
                              flexShrink: 0
                            }}
                          >
                            <span>{getSenderLabel()}</span>
                            <span style={{ marginLeft: 8, fontSize: 11, fontFamily: 'monospace' }}>
                              {formatMessageTime(msg.created_at)}
                            </span>
                          </div>
                          {/* 消息内容 */}
                          <div
                            className="message-content"
                            style={{
                              padding: '10px 14px',
                              borderRadius: 8,
                              backgroundColor: isAgent ? '#1890ff' : '#fff',
                              color: isAgent ? '#fff' : '#000',
                              boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                            }}
                          >
                            <div className="message-text">{msg.content}</div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input">
              <Input.TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault()
                    sendMessage()
                  }
                }}
                placeholder="输入消息..."
                rows={3}
              />
              <Button type="primary" onClick={sendMessage}>
                发送
              </Button>
            </div>
          </>
        ) : (
          <Empty description="选择一个会话开始聊天" />
        )}
      </div>
    </div>
  )
}

export default ChatWorkplace