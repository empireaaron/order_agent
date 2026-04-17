import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Card, Modal, Form, Input, Upload, message, Space, Tag, Select } from 'antd'
import { PlusOutlined, UploadOutlined, SettingOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'

interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  status: string
  created_at: string
}

interface KnowledgeFormValues {
  name: string
  description?: string
  status: string
}

const KnowledgeBasePage: React.FC = () => {
  const navigate = useNavigate()
  const [kbs, setKbs] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(false)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })

  const fetchKbs = async (page = pagination.current, pageSize = pagination.pageSize) => {
    setLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const response = await api.get('/knowledge/', { params: { skip, limit: pageSize } })
      setKbs(response.data)
      setPagination(prev => ({ ...prev, current: page, pageSize, total: response.data.length < pageSize ? skip + response.data.length : skip + response.data.length + 1 }))
    } catch (error) {
      console.error('Failed to fetch knowledge bases:', error)
      message.error('获取知识库列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKbs(1, pagination.pageSize)
  }, [])

  const handleCreate = async (values: KnowledgeFormValues) => {
    try {
      await api.post('/knowledge/', values)
      message.success('知识库创建成功')
      setIsModalVisible(false)
      form.resetFields()
      fetchKbs(1, pagination.pageSize)
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleDelete = async (record: KnowledgeBase) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除知识库 "${record.name}" 吗？此操作将同时删除所有关联文档和向量数据，且不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/knowledge/${record.id}`)
          message.success('知识库删除成功')
          fetchKbs(pagination.current, pagination.pageSize)
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '文档数',
      dataIndex: 'document_count',
      key: 'document_count',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'orange'}>
          {status === 'active' ? '正常' : status === 'inactive' ? '停用' : status}
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
      width: 280,
      render: (record: KnowledgeBase) => (
        <Space>
          <Button
            type="primary"
            icon={<SettingOutlined />}
            onClick={() => navigate(`/knowledge/${record.id}`)}
          >
            管理
          </Button>
          <Upload
            customRequest={async ({ file, onSuccess, onError }) => {
              try {
                const formData = new FormData()
                formData.append('file', file)
                await api.post(`/knowledge/${record.id}/documents`, formData, {
                  headers: { 'Content-Type': 'multipart/form-data' },
                })
                message.success(`${(file as File).name} 上传成功`)
                onSuccess?.('ok')
                fetchKbs(pagination.current, pagination.pageSize)
              } catch (error) {
                message.error(`${(file as File).name} 上传失败`)
                onError?.(error as Error)
              }
            }}
          >
            <Button icon={<UploadOutlined />}>上传</Button>
          </Upload>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1>知识库管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          创建知识库
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={kbs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`
          }}
          onChange={(newPagination) => fetchKbs(newPagination.current, newPagination.pageSize)}
        />
      </Card>

      <Modal
        title="创建知识库"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical" initialValues={{ status: 'active' }}>
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入知识库名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea />
          </Form.Item>
          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Select.Option value="active">正常</Select.Option>
              <Select.Option value="inactive">停用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgeBasePage