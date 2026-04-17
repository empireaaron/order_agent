import React, { useState, useEffect } from 'react'
import { Table, Tag, Button, Space, Card, Input, Modal, Form, Select, message } from 'antd'
import type { TablePaginationConfig } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'
import api from '../services/api'
import { getPriorityColor, getStatusColor } from '../utils/formatters'

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

interface TicketFormValues {
  title: string
  content: string
  priority: string
  category: string
  customer_info?: {
    contact?: string
  }
}

const TicketListPage: React.FC = () => {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })

  const fetchTickets = async (page = pagination.current, pageSize = pagination.pageSize) => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const response = await api.get('/tickets/', { params: { skip, limit: pageSize } })
      setTickets(response.data)
      // 如果后端返回总数，应更新 total；当前后端未返回总数，使用已加载数据长度估算
      setPagination(prev => ({ ...prev, current: page, pageSize, total: response.data.length < pageSize ? skip + response.data.length : skip + response.data.length + 1 }))
    } catch (error) {
      console.error('Failed to fetch tickets:', error)
      message.error('获取工单列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets(1, pagination.pageSize)
  }, [])

  const handleCreateTicket = async (values: TicketFormValues) => {
    setSubmitting(true)
    try {
      await api.post('/tickets/', values)
      message.success('工单创建成功')
      setIsModalVisible(false)
      form.resetFields()
      fetchTickets(1, pagination.pageSize)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建工单失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    fetchTickets(newPagination.current || 1, newPagination.pageSize || 10)
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
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`
          }}
          onChange={handleTableChange}
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