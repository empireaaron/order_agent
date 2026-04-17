import React, { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Statistic,
  Tabs,
  Table,
  Radio,
  Skeleton,
  Tag,
  Space,
  Typography,
  Button,
  Progress,
  DatePicker,
  message,
} from 'antd'
import {
  LineChartOutlined,
  DashboardOutlined,
  ApiOutlined,
  BugOutlined,
  WifiOutlined,
  AimOutlined,
  CheckCircleOutlined,
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

const { TabPane } = Tabs
const { Title } = Typography

// 数据类型定义
interface IntentMetricsData {
  total_classifications: number
  accuracy: number
  period_days: number
  by_intent: Record<string, {
    total: number
    accuracy: number
    sampled?: number
    sampled_correct?: number
    sampled_accuracy?: number
  }>
}

interface ApiMetricsData {
  [key: string]: {
    count: number
    avg_latency_ms: number
    p50_ms: number
    p95_ms: number
    p99_ms: number
    max_ms: number
    error_count?: number
    min_ms?: number
    source?: string
  }
}

interface ErrorMetricsData {
  [key: string]: number
}

interface WebSocketMetricsData {
  total_connections: number
  active_connections: number
  messages_sent: number
  messages_received: number
}

// 抽样标注相关类型
interface SampleStats {
  period_days: number
  total_logs: number
  sampled: number
  annotated: number
  correct: number
  sampled_accuracy: number
  by_intent: Record<string, {
    annotated: number
    correct: number
    accuracy: number
  }>
}

// 时间范围类型
type TimeRange = '1' | '7' | '30' | 'custom'

// 颜色配置
const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa541c']
const CATEGORY_COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1']

const MetricsPage: React.FC = () => {
  const navigate = useNavigate()
  const [timeRange, setTimeRange] = useState<TimeRange>('7')
  const [customDateRange, setCustomDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [loading, setLoading] = useState(true)

  // 数据状态
  const [intentData, setIntentData] = useState<IntentMetricsData | null>(null)
  const [intentTrendData, setIntentTrendData] = useState<any[]>([])
  const [apiData, setApiData] = useState<ApiMetricsData | null>(null)
  const [errorData, setErrorData] = useState<ErrorMetricsData | null>(null)
  const [wsData, setWsData] = useState<WebSocketMetricsData | null>(null)

  // 抽样标注状态
  const [sampleStats, setSampleStats] = useState<SampleStats | null>(null)

  // 获取所有数据
  const fetchData = async () => {
    // 自定义模式下未选择日期范围时不调用接口
    if (timeRange === 'custom' && !customDateRange) {
      return
    }

    setLoading(true)
    try {
      let intentUrl, trendUrl, apiUrl, errorUrl

      if (timeRange === 'custom' && customDateRange) {
        const startDate = customDateRange[0].format('YYYY-MM-DD')
        const endDate = customDateRange[1].format('YYYY-MM-DD')
        const days = customDateRange[1].diff(customDateRange[0], 'day') + 1
        intentUrl = `/metrics/intent?start_date=${startDate}&end_date=${endDate}`
        trendUrl = `/metrics/intent/trend?start_date=${startDate}&end_date=${endDate}`
        apiUrl = `/metrics/api?time_window_minutes=${days * 24 * 60}`
        errorUrl = `/metrics/errors?start_date=${startDate}&end_date=${endDate}`
      } else {
        const days = parseInt(timeRange)
        intentUrl = `/metrics/intent?days=${days}`
        trendUrl = `/metrics/intent/trend?days=${days}`
        apiUrl = `/metrics/api?time_window_minutes=${days * 24 * 60}`
        errorUrl = `/metrics/errors?days=${days}`
      }

      const [intentRes, intentTrendRes, apiRes, errorRes, wsRes] = await Promise.all([
        api.get(intentUrl),
        api.get(trendUrl),
        api.get(apiUrl),
        api.get(errorUrl),
        api.get('/metrics/websocket'),
      ])

      setIntentData(intentRes.data)
      setIntentTrendData(intentTrendRes.data.data || [])
      setApiData(apiRes.data)
      setErrorData(errorRes.data)
      setWsData(wsRes.data)
    } catch (error) {
      console.error('获取监控数据失败:', error)
      message.error('获取监控数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // 同时刷新抽样标注统计数据
    fetchSampleStats()
  }, [timeRange, customDateRange])

  // 获取抽样统计
  const fetchSampleStats = async () => {
    // 自定义模式下未选择日期范围时不调用接口
    if (timeRange === 'custom' && !customDateRange) {
      return
    }
    try {
      let url = '/metrics/intent/sample-stats?'
      if (timeRange === 'custom' && customDateRange) {
        url += `start_date=${customDateRange[0].format('YYYY-MM-DD')}&end_date=${customDateRange[1].format('YYYY-MM-DD')}`
      } else {
        url += `days=${parseInt(timeRange)}`
      }
      const res = await api.get(url)
      setSampleStats(res.data)
    } catch (error) {
      console.error('获取抽样统计失败:', error)
      message.error('获取抽样统计失败')
    }
  }

  // Tab切换时刷新抽样统计
  const handleTabChange = (key: string) => {
    if (key === 'sampling') {
      fetchSampleStats()
    }
  }

  // 计算概览数据
  const overviewStats = useMemo(() => {
    const intentTotal = intentData?.total_classifications || 0
    const intentAccuracy = intentData?.accuracy || 0

    let apiTotalRequests = 0
    let apiTotalErrors = 0
    if (apiData) {
      Object.values(apiData).forEach((item) => {
        apiTotalRequests += item.count || 0
        apiTotalErrors += item.error_count || 0
      })
    }
    const apiErrorRate = apiTotalRequests > 0 ? (apiTotalErrors / apiTotalRequests) : 0

    let errorTotal = 0
    if (errorData) {
      errorTotal = Object.values(errorData).reduce((sum, count) => sum + count, 0)
    }

    return {
      intentTotal,
      intentAccuracy,
      apiTotalRequests,
      apiErrorRate,
      errorTotal,
      wsActive: wsData?.active_connections || 0,
    }
  }, [intentData, apiData, errorData, wsData])

  // 意图识别表格数据
  const intentTableData = useMemo(() => {
    if (!intentData?.by_intent) return []
    return Object.entries(intentData.by_intent).map(([intent, data]) => ({
      intent,
      total: data.total,
      correct: Math.round(data.total * data.accuracy),
      accuracy: data.accuracy,
      sampled: data.sampled || 0,
      sampled_correct: data.sampled_correct || 0,
      sampled_accuracy: data.sampled_accuracy || 0,
    }))
  }, [intentData])

  // API 性能表格数据
  const apiTableData = useMemo(() => {
    if (!apiData) return []
    return Object.entries(apiData).map(([endpoint, data]) => {
      const [method, ...pathParts] = endpoint.split(' ')
      return {
        key: endpoint,
        endpoint: pathParts.join(' '),
        method,
        count: data.count,
        errorCount: data.error_count || 0,
        avgLatency: data.avg_latency_ms,
        maxLatency: data.max_ms,
      }
    })
  }, [apiData])

  // API 图表数据
  const apiChartData = useMemo(() => {
    if (!apiData) return []
    return Object.entries(apiData)
      .map(([endpoint, data]) => ({
        name: endpoint.length > 30 ? endpoint.substring(0, 30) + '...' : endpoint,
        fullName: endpoint,
        avgLatency: data.avg_latency_ms,
        maxLatency: data.max_ms,
      }))
      .sort((a, b) => b.avgLatency - a.avgLatency)
      .slice(0, 10)
  }, [apiData])

  // 错误统计表格数据
  const errorTableData = useMemo(() => {
    if (!errorData) return []
    const total = Object.values(errorData).reduce((sum, count) => sum + count, 0)
    return Object.entries(errorData).map(([key, count]) => {
      const [errorType, endpoint] = key.split(':')
      return {
        key,
        errorType,
        endpoint: endpoint || '-',
        count,
        percentage: total > 0 ? (count / total) : 0,
      }
    }).sort((a, b) => b.count - a.count)
  }, [errorData])

  // 错误图表数据
  const errorChartData = useMemo(() => {
    if (!errorData) return []
    // 按错误类型聚合
    const typeMap: Record<string, number> = {}
    Object.entries(errorData).forEach(([key, count]) => {
      const [errorType] = key.split(':')
      typeMap[errorType] = (typeMap[errorType] || 0) + count
    })
    return Object.entries(typeMap).map(([name, value]) => ({ name, value }))
  }, [errorData])


  // 表格列定义
  const intentColumns = [
    {
      title: '意图类型',
      dataIndex: 'intent',
      key: 'intent',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '总识别次数',
      dataIndex: 'total',
      key: 'total',
      sorter: (a: any, b: any) => a.total - b.total,
    },
    {
      title: '正确次数',
      dataIndex: 'correct',
      key: 'correct',
    },
    {
      title: '准确率',
      dataIndex: 'accuracy',
      key: 'accuracy',
      render: (accuracy: number) => {
        if (accuracy === 0) return <span style={{ color: '#999' }}>-</span>
        const percent = (accuracy * 100).toFixed(2)
        let color = 'green'
        if (accuracy < 0.8) color = 'red'
        else if (accuracy < 0.9) color = 'orange'
        return <Tag color={color}>{percent}%</Tag>
      },
      sorter: (a: any, b: any) => a.accuracy - b.accuracy,
    },
    {
      title: '抽样次数',
      dataIndex: 'sampled',
      key: 'sampled',
      sorter: (a: any, b: any) => a.sampled - b.sampled,
    },
    {
      title: '抽样正确',
      dataIndex: 'sampled_correct',
      key: 'sampled_correct',
    },
    {
      title: '抽样准确率',
      dataIndex: 'sampled_accuracy',
      key: 'sampled_accuracy',
      render: (accuracy: number, record: any) => {
        if (record.sampled === 0) return <span style={{ color: '#999' }}>-</span>
        const percent = (accuracy * 100).toFixed(2)
        let color = 'green'
        if (accuracy < 0.8) color = 'red'
        else if (accuracy < 0.9) color = 'orange'
        return <Tag color={color}>{percent}%</Tag>
      },
      sorter: (a: any, b: any) => a.sampled_accuracy - b.sampled_accuracy,
    },
  ]

  const apiColumns = [
    {
      title: '端点路径',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true,
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      render: (method: string) => {
        const colorMap: Record<string, string> = {
          GET: 'blue',
          POST: 'green',
          PUT: 'orange',
          DELETE: 'red',
          PATCH: 'purple',
        }
        return <Tag color={colorMap[method] || 'default'}>{method}</Tag>
      },
    },
    {
      title: '请求次数',
      dataIndex: 'count',
      key: 'count',
      sorter: (a: any, b: any) => a.count - b.count,
    },
    {
      title: '错误次数',
      dataIndex: 'errorCount',
      key: 'errorCount',
      render: (count: number) => count > 0 ? <Tag color="red">{count}</Tag> : <span>{count}</span>,
    },
    {
      title: '平均响应时间(ms)',
      dataIndex: 'avgLatency',
      key: 'avgLatency',
      render: (val: number) => {
        let color = 'green'
        if (val > 500) color = 'red'
        else if (val > 200) color = 'orange'
        return <span style={{ color }}>{val.toFixed(2)}</span>
      },
      sorter: (a: any, b: any) => a.avgLatency - b.avgLatency,
    },
    {
      title: '最大响应时间(ms)',
      dataIndex: 'maxLatency',
      key: 'maxLatency',
      render: (val: number) => val?.toFixed(2) || '-',
    },
  ]

  const errorColumns = [
    {
      title: '错误类型',
      dataIndex: 'errorType',
      key: 'errorType',
      render: (text: string) => <Tag color="red">{text}</Tag>,
    },
    {
      title: '发生端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true,
      render: (text: string) => text === '-' ? <span style={{ color: '#999' }}>-</span> : text,
    },
    {
      title: '发生次数',
      dataIndex: 'count',
      key: 'count',
      sorter: (a: any, b: any) => a.count - b.count,
    },
    {
      title: '占比',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (val: number) => `${(val * 100).toFixed(2)}%`,
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          <DashboardOutlined style={{ marginRight: 8 }} />
          系统监控
        </Title>
        <Space>
          <Radio.Group
            value={timeRange}
            onChange={(e) => {
              setTimeRange(e.target.value)
              if (e.target.value !== 'custom') {
                setCustomDateRange(null)
              }
            }}
            optionType="button"
            buttonStyle="solid"
          >
            <Radio.Button value="1">今日</Radio.Button>
            <Radio.Button value="7">近7天</Radio.Button>
            <Radio.Button value="30">近30天</Radio.Button>
            <Radio.Button value="custom">自定义</Radio.Button>
          </Radio.Group>
          {timeRange === 'custom' && (
            <DatePicker.RangePicker
              value={customDateRange}
              onChange={(dates) => setCustomDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              allowClear={false}
            />
          )}
        </Space>
      </div>

      {/* 概览卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Statistic
              title="意图识别总次数"
              value={overviewStats.intentTotal}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Statistic
              title="意图识别准确率"
              value={overviewStats.intentAccuracy > 0 ? (overviewStats.intentAccuracy * 100).toFixed(2) : '-'}
              suffix={overviewStats.intentAccuracy > 0 ? '%' : ''}
              prefix={<AimOutlined />}
              valueStyle={{ color: overviewStats.intentAccuracy >= 0.9 ? '#52c41a' : overviewStats.intentAccuracy >= 0.8 ? '#faad14' : '#f5222d' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Statistic
              title="API 总请求数"
              value={overviewStats.apiTotalRequests}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Statistic
              title="API 错误率"
              value={overviewStats.apiErrorRate * 100}
              suffix="%"
              prefix={<BugOutlined />}
              valueStyle={{ color: overviewStats.apiErrorRate > 0.05 ? '#f5222d' : '#52c41a' }}
              loading={loading}
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Statistic
              title="错误总数"
              value={overviewStats.errorTotal}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#faad14' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Statistic
              title="WebSocket 活跃连接"
              value={overviewStats.wsActive}
              prefix={<WifiOutlined />}
              valueStyle={{ color: '#722ed1' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* Tabs 标签页 */}
      <Card style={{ marginTop: '24px' }}>
        <Tabs defaultActiveKey="intent" onChange={handleTabChange}>
          {/* 意图识别 Tab */}
          <TabPane
            tab={
              <Space>
                <LineChartOutlined />
                意图识别
              </Space>
            }
            key="intent"
          >
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <Card title="意图识别趋势" size="small">
                  {loading ? (
                    <Skeleton active paragraph={{ rows: 6 }} />
                  ) : intentTrendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={intentTrendData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="date"
                          tickFormatter={(value) => dayjs(value).format('MM-DD')}
                        />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        {Object.keys(intentTrendData[0] || {}).filter(k => k !== 'date').map((intent, index) => (
                          <Line
                            key={intent}
                            type="monotone"
                            dataKey={intent}
                            stroke={COLORS[index % COLORS.length]}
                            strokeWidth={2}
                            dot={false}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                      暂无数据
                    </div>
                  )}
                </Card>
              </Col>
              <Col xs={24} style={{ marginTop: '16px' }}>
                <Card title="意图识别详情" size="small">
                  <Table
                    dataSource={intentTableData}
                    columns={intentColumns}
                    rowKey="intent"
                    loading={loading}
                    pagination={false}
                    size="small"
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* API 性能 Tab */}
          <TabPane
            tab={
              <Space>
                <ApiOutlined />
                API 性能
              </Space>
            }
            key="api"
          >
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <Card title="平均响应时间 TOP10" size="small">
                  {loading ? (
                    <Skeleton active paragraph={{ rows: 6 }} />
                  ) : apiChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={apiChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" unit="ms" />
                        <YAxis dataKey="name" type="category" width={200} tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="avgLatency" name="平均响应时间" fill="#1890ff" />
                        <Bar dataKey="maxLatency" name="最大响应时间" fill="#f5222d" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                      暂无数据
                    </div>
                  )}
                </Card>
              </Col>
              <Col xs={24} style={{ marginTop: '16px' }}>
                <Card title="API 性能详情" size="small">
                  <Table
                    dataSource={apiTableData}
                    columns={apiColumns}
                    rowKey="key"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                    size="small"
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* 错误统计 Tab */}
          <TabPane
            tab={
              <Space>
                <BugOutlined />
                错误统计
              </Space>
            }
            key="error"
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="错误类型分布" size="small">
                  {loading ? (
                    <Skeleton active paragraph={{ rows: 6 }} />
                  ) : errorChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={errorChartData}
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
                          {errorChartData.map((_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                      暂无错误数据
                    </div>
                  )}
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="错误详情" size="small">
                  <Table
                    dataSource={errorTableData}
                    columns={errorColumns}
                    rowKey="key"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                    size="small"
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* 抽样标注 Tab */}
          <TabPane
            tab={
              <Space>
                <CheckCircleOutlined />
                抽样标注
              </Space>
            }
            key="sampling"
          >
            <Row gutter={[16, 16]}>
              {/* 抽样统计概览 */}
              <Col xs={24}>
                <Card size="small">
                  <Row gutter={[16, 16]} align="middle">
                    <Col xs={24} sm={6}>
                      <Statistic
                        title="总记录数"
                        value={sampleStats?.total_logs || 0}
                        loading={!sampleStats}
                      />
                    </Col>
                    <Col xs={24} sm={6}>
                      <Statistic
                        title="已抽样"
                        value={sampleStats?.sampled || 0}
                        suffix={`/ ${sampleStats?.total_logs || 0}`}
                        loading={!sampleStats}
                      />
                    </Col>
                    <Col xs={24} sm={6}>
                      <Statistic
                        title="已标注"
                        value={sampleStats?.annotated || 0}
                        loading={!sampleStats}
                      />
                    </Col>
                    <Col xs={24} sm={6}>
                      <div>
                        <div style={{ marginBottom: 8 }}>抽样准确率</div>
                        <Progress
                          percent={Math.round((sampleStats?.sampled_accuracy || 0) * 100)}
                          status={
                            (sampleStats?.sampled_accuracy || 0) >= 0.9
                              ? 'success'
                              : (sampleStats?.sampled_accuracy || 0) >= 0.8
                              ? 'normal'
                              : 'exception'
                          }
                          format={(percent) => `${percent}%`}
                        />
                      </div>
                    </Col>
                  </Row>
                  <Row style={{ marginTop: 16 }}>
                    <Col xs={24}>
                      <Button type="primary" onClick={() => navigate('/sampling-annotation')}>
                        去标注
                      </Button>
                      <span style={{ marginLeft: 16, color: '#999' }}>
                        前往抽样标注页面进行样本抽取和人工标注
                      </span>
                    </Col>
                  </Row>
                </Card>
              </Col>

              {/* 按意图统计 */}
              <Col xs={24}>
                {sampleStats && sampleStats.annotated > 0 ? (
                  <Card title="按意图统计" size="small">
                    <Row gutter={[16, 16]}>
                      {Object.entries(sampleStats?.by_intent || {}).map(([intent, data]) => (
                        <Col xs={24} sm={12} md={8} key={intent}>
                          <Card size="small">
                            <div>
                              <Tag color="blue">{intent}</Tag>
                            </div>
                            <div style={{ marginTop: 8 }}>
                              标注数: {data.annotated} | 正确: {data.correct}
                            </div>
                            <Progress
                              percent={Math.round(data.accuracy * 100)}
                              size="small"
                              status={data.accuracy >= 0.9 ? 'success' : data.accuracy >= 0.8 ? 'normal' : 'exception'}
                              format={(percent) => `${percent}%`}
                            />
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  </Card>
                ) : (
                  <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
                    <CheckCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                    <p>暂无标注数据</p>
                    <p style={{ fontSize: 12 }}>点击上方"去标注"按钮进行样本抽取和人工标注</p>
                  </div>
                )}
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default MetricsPage
