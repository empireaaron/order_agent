import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Tag,
  Space,
  Typography,
  Progress,
  message,
  Radio,
  DatePicker,
  InputNumber,
} from 'antd'
import {
  CheckCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons'
import api from '../services/api'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography
const { RangePicker } = DatePicker

// 数据类型定义
interface SampleLog {
  log_id: string
  intent: string
  user_input: string | null
  confidence: number
  created_at: string
}

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

const SamplingAnnotationPage: React.FC = () => {
  const navigate = useNavigate()
  
  // 时间范围状态
  const [timeRange, setTimeRange] = useState<TimeRange>('7')
  const [customDateRange, setCustomDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

  // 抽样标注状态
  const [sampleStats, setSampleStats] = useState<SampleStats | null>(null)
  const [sampleLogs, setSampleLogs] = useState<SampleLog[]>([])
  const [samplingLoading, setSamplingLoading] = useState(false)
  const [annotatingId, setAnnotatingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [sampleLimit, setSampleLimit] = useState<number>(10)

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

  // 抽取样本
  const handleSample = async () => {
    // 自定义模式下未选择日期范围时不抽取
    if (timeRange === 'custom' && !customDateRange) {
      message.warning('请先选择日期范围')
      return
    }
    setSamplingLoading(true)
    try {
      let url = `/metrics/intent/sample?limit=${sampleLimit}&`
      if (timeRange === 'custom' && customDateRange) {
        url += `start_date=${customDateRange[0].format('YYYY-MM-DD')}&end_date=${customDateRange[1].format('YYYY-MM-DD')}`
      } else {
        url += `days=${parseInt(timeRange)}`
      }
      const res = await api.get(url)
      setSampleLogs(res.data)
      await fetchSampleStats()
      message.success(`成功抽取 ${res.data.length} 条记录`)
      // 重置抽样数量
      setSampleLimit(10)
    } catch (error) {
      message.error('抽取样本失败')
    } finally {
      setSamplingLoading(false)
    }
  }

  // 提交标注
  const handleAnnotate = async (logId: string, isCorrect: boolean) => {
    setAnnotatingId(logId)
    try {
      await api.post('/metrics/intent/annotate', {
        log_id: logId,
        is_correct: isCorrect,
      })
      message.success('标注成功')
      // 移除已标注的记录
      setSampleLogs((prev) => prev.filter((log) => log.log_id !== logId))
      await fetchSampleStats()
    } catch (error) {
      message.error('标注失败')
    } finally {
      setAnnotatingId(null)
    }
  }

  useEffect(() => {
    setLoading(true)
    fetchSampleStats().finally(() => setLoading(false))
  }, [timeRange, customDateRange])

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          <CheckCircleOutlined style={{ marginRight: 8 }} />
          抽样标注
        </Title>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/metrics')}>
          返回监控
        </Button>
      </div>

      {/* 时间范围选择 */}
      <Card size="small" style={{ marginBottom: 16 }}>
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
            <RangePicker
              value={customDateRange}
              onChange={(dates) => setCustomDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              allowClear={false}
            />
          )}
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        {/* 抽样统计概览 */}
        <Col xs={24}>
          <Card size="small" loading={loading}>
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={6}>
                <Statistic
                  title="总记录数"
                  value={sampleStats?.total_logs || 0}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="已抽样"
                  value={sampleStats?.sampled || 0}
                  suffix={`/ ${sampleStats?.total_logs || 0}`}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="已标注"
                  value={sampleStats?.annotated || 0}
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
          </Card>
        </Col>

        {/* 抽取样本按钮 */}
        <Col xs={24}>
          <Card size="small">
            <Space>
              <InputNumber
                min={1}
                max={50}
                value={sampleLimit}
                onChange={(value) => setSampleLimit(value || 10)}
                disabled={sampleLogs.length > 0 || samplingLoading}
                addonBefore="抽样数量"
                style={{ width: 150 }}
              />
              <Button
                type="primary"
                onClick={handleSample}
                loading={samplingLoading}
                disabled={sampleLogs.length > 0}
              >
                抽取样本
              </Button>
            </Space>
            <span style={{ marginLeft: 16, color: '#999' }}>
              {sampleLogs.length > 0 && '请先完成当前样本的标注'}
              {sampleLogs.length === 0 && '随机抽取样本进行人工标注，用于验证AI意图识别准确率'}
            </span>
          </Card>
        </Col>

        {/* 待标注样本列表 */}
        <Col xs={24}>
          {sampleLogs.length > 0 && (
            <Card title="待标注样本" size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                {sampleLogs.map((log) => (
                  <Card
                    key={log.log_id}
                    size="small"
                    type="inner"
                    title={
                      <Space>
                        <Tag color="blue">{log.intent}</Tag>
                        <span style={{ color: '#999', fontSize: 12 }}>
                          置信度: {(log.confidence * 100).toFixed(1)}%
                        </span>
                      </Space>
                    }
                    actions={[
                      <Button
                        key="correct"
                        type="primary"
                        icon={<CheckOutlined />}
                        size="small"
                        loading={annotatingId === log.log_id}
                        onClick={() => handleAnnotate(log.log_id, true)}
                      >
                        正确
                      </Button>,
                      <Button
                        key="incorrect"
                        danger
                        icon={<CloseOutlined />}
                        size="small"
                        loading={annotatingId === log.log_id}
                        onClick={() => handleAnnotate(log.log_id, false)}
                      >
                        错误
                      </Button>,
                    ]}
                  >
                    <p><strong>用户输入:</strong></p>
                    <p style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                      {log.user_input || '（无内容）'}
                    </p>
                    <p style={{ color: '#999', fontSize: 12 }}>
                      识别意图: <Tag>{log.intent}</Tag>
                    </p>
                  </Card>
                ))}
              </Space>
            </Card>
          )}

          {sampleLogs.length === 0 && sampleStats && sampleStats.annotated > 0 && (
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
          )}

          {sampleLogs.length === 0 && sampleStats?.annotated === 0 && (
            <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
              <CheckCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <p>点击上方"抽取样本"按钮开始人工标注</p>
              <p style={{ fontSize: 12 }}>抽样标注用于验证AI意图识别的真实准确率</p>
            </div>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default SamplingAnnotationPage
