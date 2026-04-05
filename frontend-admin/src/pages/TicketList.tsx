import React, { useState, useEffect } from 'react'
import { Table, Tag, Button, Space, Card, Input, Modal, Form, Select, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'
import api from '../services/api'

const { TextArea } = Input
const { Option } = Select

interface Ticket {
  id: string
  ticket_no: string
  title: string
  priority: string
  category: string
  status: string
  customer_id: string
  created_at: string
}

const TicketListPage: React.FC = () => {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const fetchTickets = async () => {
    setLoading(true)
    try {
      const response = await api.get('/tickets/')
      setTickets(response.data)
    } catch (error) {
      console.error('Failed to fetch tickets:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()
  }, [])

  const handleCreateTicket = async (values: any) => {
    setSubmitting(true)
    try {
      await api.post('/tickets/', values)
      message.success('工单创建成功')
      setIsModalVisible(false)
      form.resetFields()
      fetchTickets()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建工单失败')
    } finally {
      setSubmitting(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'green',
      normal: 'blue',
      high: 'orange',
      urgent: 'red',
    }
    return colors[priority] || 'default'
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      open: 'blue',
      pending: 'orange',
      in_progress: 'cyan',
      resolved: 'green',
      closed: 'default',
    }
    return colors[status] || 'default'
  }

  const columns = [
    {
      title: '工单编号',
      dataIndex: 'ticket_no',
      key: 'ticket_no',
      width: 150,
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
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>
          {priority.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status}
        </Tag>
      ),
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
      width: 120,
      render: (_: unknown, record: Ticket) => (
        <Button type="link" onClick={() => navigate(`/tickets/${record.id}`)}>
          查看详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>工单管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          创建工单
        </Button>
      </div>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="搜索工单..."
            allowClear
            style={{ width: 300 }}
            prefix={<SearchOutlined />}
          />
        </div>

        <Table
          columns={columns}
          dataSource={tickets}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="创建工单"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        width={600}
      >
        <Form
          form={form}
          onFinish={handleCreateTicket}
          layout="vertical"
          initialValues={{
            priority: 'normal',
            category: 'general',
          }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入工单标题' }]}
          >
            <Input placeholder="请输入工单标题" />
          </Form.Item>

          <Form.Item
            name="content"
            label="内容"
            rules={[{ required: true, message: '请输入工单内容' }]}
          >
            <TextArea rows={4} placeholder="请详细描述您的问题" />
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
            rules={[{ required: true, message: '请选择优先级' }]}
          >
            <Select placeholder="请选择优先级">
              <Option value="low">低</Option>
              <Option value="normal">普通</Option>
              <Option value="high">高</Option>
              <Option value="urgent">紧急</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select placeholder="请选择分类">
              <Option value="technical">技术问题</Option>
              <Option value="billing">计费问题</Option>
              <Option value="account">账户问题</Option>
              <Option value="general">一般咨询</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name={['customer_info', 'contact']}
            label="联系方式"
          >
            <Input placeholder="手机号或邮箱（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TicketListPage