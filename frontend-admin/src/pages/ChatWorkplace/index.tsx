import React, { useState, useEffect, useRef } from 'react'
import { Card, Badge, Button, List, Avatar, Input, Tag, Empty, Spin, Modal, message } from 'antd'
import { MessageOutlined, UserOutlined, CloseOutlined, TeamOutlined } from '@ant-design/icons'
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

interface WaitingSession {
  id: string
  customer: {
    id: string
    username: string
    email: string
  }
  request_type: string
  initial_message: string
  created_at: string
  wait_time_seconds: number
}

interface WebSocketMessage {
  type: 'new_message' | 'new_waiting_session' | 'session_assigned' | 'session_closed'
  session_id?: string
  message?: ChatMessage
  customer?: {
    id: string
    username: string
  }
  initial_message?: string
}

const ChatWorkplace: React.FC = () => {
  const { user, token } = useAuthStore()
  const [online, setOnline] = useState(false)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [waitingSessions, setWaitingSessions] = useState<WaitingSession[]>([])
  const [waitingModalVisible, setWaitingModalVisible] = useState(false)
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const requestIdRef = useRef<number>(0)
  // 使用 ref 存储 activeSession，避免 WebSocket 回调中的闭包问题
  const activeSessionRef = useRef<ChatSession | null>(null)

  // 同步 activeSession 到 ref
  useEffect(() => {
    activeSessionRef.current = activeSession
  }, [activeSession])

  // 建立WebSocket连接
  useEffect(() => {
    if (!online) {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    if (!token) {
      console.error('No token found for WebSocket connection')
      return
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/chat?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Chat WebSocket connected')
      fetchSessions()
      fetchWaitingQueue()
      // 每10秒刷新一次等待队列
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      intervalRef.current = setInterval(() => {
        if (online) {
          fetchWaitingQueue()
        }
      }, 10000)
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
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
      ws.close()
      wsRef.current = null
    }
  }, [online, token])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleWebSocketMessage = (data: WebSocketMessage) => {
    // 使用 ref 获取最新的 activeSession，避免闭包问题
    const currentActiveSession = activeSessionRef.current

    switch (data.type) {
      case 'new_message':
        if (data.session_id === currentActiveSession?.id && data.message) {
          setMessages(prev => [...prev, data.message as ChatMessage])
        } else if (data.message) {
          setSessions(prev => prev.map(s =>
            s.id === data.session_id
              ? { ...s, unread_count: s.unread_count + 1, last_message: data.message!.content }
              : s
          ))
        }
        break
      case 'new_waiting_session':
        fetchWaitingQueue()
        break
      case 'session_assigned':
        // 有新会话分配给自己，刷新会话列表
        fetchSessions()
        fetchWaitingQueue()
        break
      case 'session_closed':
        // 会话被关闭，刷新会话列表
        if (data.session_id === currentActiveSession?.id) {
          setActiveSession(null)
        }
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
      message.error('获取会话列表失败')
    }
  }

  const fetchWaitingQueue = async () => {
    try {
      const response = await api.get('/chat-service/sessions/waiting')
      console.log('Fetched waiting queue:', response.data)
      setWaitingSessions(response.data)
    } catch (error) {
      console.error('Failed to fetch waiting queue:', error)
      message.error('获取等待队列失败')
    }
  }

  const goOnline = async () => {
    try {
      await api.post('/chat-service/agent/online')
      setOnline(true)
    } catch (error) {
      console.error('Failed to go online:', error)
      message.error('上线失败')
    }
  }

  const goOffline = async () => {
    try {
      await api.post('/chat-service/agent/offline')
      setOnline(false)
      setActiveSession(null)
    } catch (error) {
      console.error('Failed to go offline:', error)
      message.error('下线失败')
    }
  }

  const acceptSession = async (sessionId: string) => {
    try {
      await api.post(`/chat-service/sessions/${sessionId}/accept`)

      // 等待一下确保 WebSocket 连接正常
      timeoutRef.current = setTimeout(() => {
        wsRef.current?.send(JSON.stringify({
          type: 'join_session',
          session_id: sessionId,
          role: 'agent'
        }))
      }, 100)

      // 获取会话详情并设置为活动会话
      const response = await api.get(`/chat-service/sessions/my?status=connected`)
      setSessions(response.data)

      // 找到刚接入的会话并激活
      const acceptedSession = response.data.find((s: ChatSession) => s.id === sessionId)
      if (acceptedSession) {
        setActiveSession(acceptedSession)
        // 本地立即清零未读数
        setSessions(prev => prev.map(s =>
          s.id === sessionId ? { ...s, unread_count: 0 } : s
        ))
        // 加载消息
        const msgResponse = await api.get(`/chat-service/sessions/${sessionId}/messages`)
        setMessages(msgResponse.data.items || [])
        // 标记该会话中的未读消息为已读
        const unreadMessageIds = (msgResponse.data.items || [])
          .filter((msg: ChatMessage) => !msg.is_read)
          .map((msg: ChatMessage) => msg.id)
        if (unreadMessageIds.length > 0) {
          wsRef.current?.send(JSON.stringify({
            type: 'read',
            session_id: sessionId,
            message_ids: unreadMessageIds
          }))
        }
      }

      fetchWaitingQueue()
      setWaitingModalVisible(false)
    } catch (error) {
      console.error('Failed to accept session:', error)
      message.error('接入会话失败')
    }
  }

  const loadSessionMessages = async (session: ChatSession) => {
    setActiveSession(session)
    // 本地立即清零未读数，让红点消失
    setSessions(prev => prev.map(s =>
      s.id === session.id ? { ...s, unread_count: 0 } : s
    ))
    setLoading(true)
    const currentRequestId = ++requestIdRef.current
    try {
      const response = await api.get(`/chat-service/sessions/${session.id}/messages`)
      // 忽略过期请求的响应
      if (currentRequestId !== requestIdRef.current) return
      setMessages(response.data.items || [])

      // 标记该会话中的未读消息为已读
      const unreadMessageIds = (response.data.items || [])
        .filter((msg: ChatMessage) => !msg.is_read)
        .map((msg: ChatMessage) => msg.id)
      if (unreadMessageIds.length > 0) {
        wsRef.current?.send(JSON.stringify({
          type: 'read',
          session_id: session.id,
          message_ids: unreadMessageIds
        }))
      }

      wsRef.current?.send(JSON.stringify({
        type: 'join_session',
        session_id: session.id,
        role: 'agent'
      }))
    } catch (error) {
      if (currentRequestId === requestIdRef.current) {
        console.error('Failed to load messages:', error)
        message.error('加载消息失败')
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false)
      }
    }
  }

  const sendMessage = () => {
    if (!inputValue.trim() || !activeSession) return

    const content = inputValue.trim()

    // 先本地显示自己发送的消息
    const newMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      content: content,
      sender_type: 'agent',
      sender: {
        id: user?.id || '',
        name: user?.full_name || user?.username || '客服'
      },
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, newMessage])

    wsRef.current?.send(JSON.stringify({
      type: 'chat_message',
      session_id: activeSession.id,
      content: content
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
      message.error('关闭会话失败')
    }
  }

  const formatWaitTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
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
            <Badge count={waitingSessions.length} style={{ marginRight: 16 }}>
              <Button size="small" icon={<TeamOutlined />} onClick={() => {
                fetchWaitingQueue()
                setWaitingModalVisible(true)
              }}>
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
                    {item.customer?.username || '未知客户'}
                    {item.unread_count > 0 && (
                      <Badge count={item.unread_count} style={{ marginLeft: 8 }} />
                    )}
                  </span>
                }
                description={item.last_message?.slice(0, 20) + '...' || '暂无消息'}
              />
            </List.Item>
          )}
        />
      </div>

      <div className="chat-main">
        {activeSession ? (
          <>
            <div className="chat-main-header">
              <span>{activeSession.customer?.username || '未知客户'}</span>
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

      {/* 等待队列弹窗 */}
      <Modal
        title="等待接入的客户"
        open={waitingModalVisible}
        onCancel={() => setWaitingModalVisible(false)}
        footer={null}
      >
        <List
          dataSource={waitingSessions}
          renderItem={item => (
            <List.Item
              actions={[
                <Button type="primary" size="small" onClick={() => acceptSession(item.id)}>
                  接入
                </Button>
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar icon={<UserOutlined />} />}
                title={item.customer.username}
                description={
                  <>
                    <div>等待时长: {formatWaitTime(item.wait_time_seconds)}</div>
                    <div style={{ color: '#999', fontSize: 12 }}>
                      {item.initial_message?.slice(0, 50) || '无初始消息'}
                    </div>
                  </>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无等待的客户' }}
        />
      </Modal>
    </div>
  )
}

export default ChatWorkplace