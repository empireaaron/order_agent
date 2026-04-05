import React, { useState, useEffect } from 'react'
import { Table, Button, Card, Tag, Modal, Form, Input, Select, message, Space } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'

interface User {
  id: string
  username: string
  email: string
  full_name?: string
  role?: {
    id: number
    name: string
    code: string
  }
  is_active: boolean
  created_at: string
}

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const response = await api.get('/users/')
      setUsers(response.data)
    } catch (error) {
      console.error('Failed to fetch users:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleAddUser = async (values: any) => {
    setSubmitting(true)
    try {
      await api.post('/auth/register', values)
      message.success('用户创建成功')
      setIsModalOpen(false)
      form.resetFields()
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建用户失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEditUser = async (values: any) => {
    if (!editingUser) return
    setSubmitting(true)
    try {
      await api.patch(`/users/${editingUser.id}`, values)
      message.success('用户更新成功')
      setIsEditModalOpen(false)
      setEditingUser(null)
      editForm.resetFields()
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新用户失败')
    } finally {
      setSubmitting(false)
    }
  }

  const openEditModal = (user: User) => {
    setEditingUser(user)
    editForm.setFieldsValue({
      full_name: user.full_name,
      role_id: user.role?.id,
      is_active: user.is_active,
    })
    setIsEditModalOpen(true)
  }

  const handleDeleteUser = (user: User) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/users/${user.id}`)
          message.success('用户删除成功')
          fetchUsers()
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除用户失败')
        }
      },
    })
  }

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: { name: string; code: string }) => {
        const colorMap: Record<string, string> = {
          admin: 'red',
          agent: 'blue',
          operator: 'orange',
          customer: 'green'
        }
        return (
          <Tag color={colorMap[role?.code] || 'default'}>
            {role?.name || '未知'}
          </Tag>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active: boolean) => (
        <Tag color={is_active ? 'green' : 'red'}>
          {is_active ? '激活' : '禁用'}
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
      width: 150,
      render: (_: any, record: User) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEditModal(record)}>
            编辑
          </Button>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDeleteUser(record)}>
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>用户管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          添加用户
        </Button>
      </div>

      <Modal
        title="编辑用户"
        open={isEditModalOpen}
        onCancel={() => {
          setIsEditModalOpen(false)
          setEditingUser(null)
        }}
        footer={null}
      >
        <Form form={editForm} layout="vertical" onFinish={handleEditUser}>
          <Form.Item
            name="full_name"
            label="姓名"
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="role_id"
            label="角色"
          >
            <Select
              placeholder="请选择角色"
              options={[
                { value: 1, label: '管理员' },
                { value: 2, label: '客服' },
                { value: 3, label: '运营' },
                { value: 4, label: '客户' }
              ]}
            />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="状态"
          >
            <Select
              placeholder="请选择状态"
              options={[
                { value: true, label: '激活' },
                { value: false, label: '禁用' }
              ]}
            />
          </Form.Item>
          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <Button onClick={() => {
                setIsEditModalOpen(false)
                setEditingUser(null)
              }}>取消</Button>
              <Button type="primary" htmlType="submit" loading={submitting}>
                保存
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加用户"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleAddUser}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Form.Item
            name="full_name"
            label="姓名"
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="role_id"
            label="角色"
            initialValue={4}
          >
            <Select
              options={[
                { value: 1, label: '管理员' },
                { value: 2, label: '客服' },
                { value: 3, label: '运营' },
                { value: 4, label: '客户' }
              ]}
            />
          </Form.Item>
          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <Button onClick={() => setIsModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={submitting}>
                创建
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>

      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
        />
      </Card>
    </div>
  )
}

export default UsersPage