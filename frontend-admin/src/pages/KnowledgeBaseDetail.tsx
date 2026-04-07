import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Table,
  Upload,
  message,
  Descriptions,
  Tag,
  Modal,
  Space,
  Typography,
  Breadcrumb,
  Form,
  Input,
  Select
} from 'antd'
import {
  UploadOutlined,
  DeleteOutlined,
  ArrowLeftOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileMarkdownOutlined,
  EditOutlined
} from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

interface KnowledgeBase {
  id: string
  name: string
  description: string
  collection_name: string
  document_count: number
  status: string
  created_at: string
}

interface Document {
  id: string
  title: string
  original_filename: string
  file_type: string
  file_size: number
  chunk_count: number
  status: string
  error_message?: string
  created_at: string
}

const KnowledgeBaseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [kb, setKb] = useState<KnowledgeBase | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [docLoading, setDocLoading] = useState(false)
  const [isEditModalVisible, setIsEditModalVisible] = useState(false)
  const [editForm] = Form.useForm()

  const fetchKnowledgeBase = async () => {
    if (!id) return
    setLoading(true)
    try {
      const response = await api.get(`/knowledge/${id}`)
      setKb(response.data)
    } catch (error) {
      message.error('获取知识库信息失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchDocuments = async () => {
    if (!id) return
    setDocLoading(true)
    try {
      const response = await api.get(`/knowledge/${id}/documents`)
      setDocuments(response.data)
    } catch (error) {
      console.error('Failed to fetch documents:', error)
      message.error('获取文档列表失败')
    } finally {
      setDocLoading(false)
    }
  }

  useEffect(() => {
    fetchKnowledgeBase()
    fetchDocuments()
  }, [id])

  const handleUploadChange = (info: any) => {
    if (info.file.status === 'done') {
      message.success(`${info.file.name} 上传成功`)
      fetchDocuments()
      fetchKnowledgeBase()
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} 上传失败`)
    }
  }

  const handleEdit = () => {
    if (kb) {
      editForm.setFieldsValue({
        name: kb.name,
        description: kb.description,
        status: kb.status,
      })
      setIsEditModalVisible(true)
    }
  }

  const handleUpdate = async (values: any) => {
    try {
      await api.put(`/knowledge/${id}`, values)
      message.success('知识库更新成功')
      setIsEditModalVisible(false)
      fetchKnowledgeBase()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const handleDeleteDocument = (doc: Document) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文档 "${doc.original_filename}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await api.delete(`/knowledge/${id}/documents/${doc.id}`)
          message.success('文档删除成功')
          fetchDocuments()
          fetchKnowledgeBase()
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除文档失败')
        }
      },
    })
  }

  const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case '.pdf':
        return <FilePdfOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
      case '.docx':
      case '.doc':
        return <FileWordOutlined style={{ fontSize: 24, color: '#1890ff' }} />
      case '.md':
        return <FileMarkdownOutlined style={{ fontSize: 24, color: '#52c41a' }} />
      default:
        return <FileTextOutlined style={{ fontSize: 24, color: '#8c8c8c' }} />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      processing: { color: 'blue', text: '处理中' },
      indexed: { color: 'green', text: '已完成' },
      failed: { color: 'red', text: '失败' },
    }
    const { color, text } = statusMap[status] || { color: 'default', text: status }
    return <Tag color={color}>{text}</Tag>
  }

  const columns = [
    {
      title: '文档',
      key: 'document',
      render: (record: Document) => (
        <Space>
          {getFileIcon(record.file_type)}
          <div>
            <div>{record.title}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.original_filename} · {formatFileSize(record.file_size)}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string, record: Document) => (
        <div>
          {getStatusTag(status)}
          {record.error_message && (
            <div style={{ fontSize: 12, color: '#ff4d4f', marginTop: 4 }}>
              {record.error_message}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (record: Document) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteDocument(record)}
        >
          删除
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Button type="link" onClick={() => navigate('/knowledge')} style={{ padding: 0 }}>
            知识库
          </Button>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{kb?.name || '详情'}</Breadcrumb.Item>
      </Breadcrumb>

      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/knowledge')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card loading={loading} style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>{kb?.name}</Title>
          <Button icon={<EditOutlined />} onClick={handleEdit}>
            编辑
          </Button>
        </div>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="描述">{kb?.description || '-'}</Descriptions.Item>
          <Descriptions.Item label="Collection">{kb?.collection_name}</Descriptions.Item>
          <Descriptions.Item label="文档数量">{kb?.document_count || 0}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={kb?.status === 'active' ? 'green' : 'orange'}>
              {kb?.status === 'active' ? '正常' : kb?.status === 'inactive' ? '停用' : kb?.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{kb?.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title={<Title level={4}>文档列表</Title>}
        extra={
          <Upload
            customRequest={async ({ file, onSuccess, onError }) => {
              try {
                const formData = new FormData()
                formData.append('file', file)
                await api.post(`/knowledge/${id}/documents`, formData, {
                  headers: { 'Content-Type': 'multipart/form-data' },
                })
                message.success(`${(file as File).name} 上传成功`)
                onSuccess?.('ok')
                fetchDocuments()
                fetchKnowledgeBase()
              } catch (error) {
                message.error(`${(file as File).name} 上传失败`)
                onError?.(error as Error)
              }
            }}
            showUploadList={false}
          >
            <Button type="primary" icon={<UploadOutlined />}>
              上传文档
            </Button>
          </Upload>
        }
      >
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={docLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="编辑知识库"
        open={isEditModalVisible}
        onCancel={() => setIsEditModalVisible(false)}
        onOk={() => editForm.submit()}
      >
        <Form form={editForm} onFinish={handleUpdate} layout="vertical">
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
            <Input.TextArea rows={4} />
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

export default KnowledgeBaseDetailPage