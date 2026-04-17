export const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    low: 'green',
    normal: 'blue',
    high: 'orange',
    urgent: 'red',
  }
  return colors[priority] || 'default'
}

export const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    open: 'blue',
    pending: 'orange',
    in_progress: 'cyan',
    resolved: 'green',
    closed: 'default',
  }
  return colors[status] || 'default'
}
