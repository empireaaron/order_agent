/**
 * TicketBot 嵌入式客服 Widget
 * 可在任意网站嵌入使用
 *
 * 使用方法:
 * <script src="https://your-domain.com/ticket-widget.js" defer></script>
 * <script>
 *   TicketWidget.init({
 *     apiUrl: 'https://api.your-domain.com',
 *     websocketUrl: 'wss://api.your-domain.com/ws',
 *     theme: 'blue',
 *     showBubble: true
 *   });
 * </script>
 */

(function(global) {
  'use strict';

  const TicketWidget = {
    config: {
      apiUrl: '',
      websocketUrl: '',
      theme: 'blue',
      showBubble: true,
      position: 'bottom-right',
      title: '在线客服',
      welcomeMessage: '您好！我是AI智能客服助手 🤖\n\n我可以帮您：\n• 📋 创建工单 - 描述遇到的问题\n• 🔍 查询工单 - 了解处理进度\n• 💡 解答问题 - 基于知识库回答\n• 👨‍💼 转人工 - 需要人工帮助时点击右上角\n\n请直接输入您的问题~'
    },

    state: {
      isOpen: false,
      isAuthenticated: false,
      token: null,
      userId: null,
      ws: null,
      messages: [],
      chatMode: 'ai', // 'ai' 或 'human'
      chatSessionId: null,
      chatWs: null,
      isWaitingForAgent: false,
      // WebSocket 心跳相关
      wsHeartbeatInterval: null,
      chatWsHeartbeatInterval: null,
      lastPongTime: null,
      // 客服聊天记录分页
      chatHistoryPage: 1,
      chatHistoryHasMore: false,
      isLoadingHistory: false,
      historyLoadedForSession: null, // 记录已加载历史的会话ID，防止重复加载
      // AI聊天记录分页
      aiHistoryPage: 1,
      aiHistoryHasMore: false,
      isLoadingAIHistory: false
    },

    init(userConfig) {
      this.config = { ...this.config, ...userConfig };
      this.createShadowHost();
      this.createWidget();
      this.attachEventListeners();

      // 尝试从 localStorage 恢复登录状态
      this.restoreLoginState();

      if (this.config.showBubble) {
        this.showChatBubble();
      }
    },

    // 创建 Shadow DOM 宿主元素
    createShadowHost() {
      // 如果已存在则移除
      const existingHost = document.getElementById('ticket-widget-host');
      if (existingHost) {
        existingHost.remove();
      }

      // 创建宿主元素
      this.shadowHost = document.createElement('div');
      this.shadowHost.id = 'ticket-widget-host';
      document.body.appendChild(this.shadowHost);

      // 附加 Shadow DOM (closed 模式提供完全隔离)
      this.shadowRoot = this.shadowHost.attachShadow({ mode: 'closed' });

      // 创建样式元素并附加到 Shadow DOM
      const styleSheet = document.createElement('style');
      styleSheet.textContent = this.getStyles();
      this.shadowRoot.appendChild(styleSheet);

      // 创建容器元素
      this.widgetContainer = document.createElement('div');
      this.widgetContainer.className = 'ticket-widget-container';
      this.shadowRoot.appendChild(this.widgetContainer);
    },

    // 从 localStorage 恢复登录状态
    restoreLoginState() {
      try {
        const token = localStorage.getItem('widget_token');
        const userId = localStorage.getItem('widget_user_id');
        const username = localStorage.getItem('widget_username');

        if (token && userId) {
          console.log('Restoring login state from localStorage');
          this.state.token = token;
          this.state.userId = userId;
          this.state.isAuthenticated = true;

          // 验证 token 是否有效
          this.verifyToken(token).then(async (isValid) => {
            if (isValid) {
              console.log('Token is valid, re-rendering widget');
              // 重新创建 widget 以显示登录后的界面
              this.createWidget();
              this.attachEventListeners();
              // 连接系统 WebSocket（用于接收通知）
              this.connectWebSocket();
              // 连接聊天 WebSocket，等待 session_rejoined 事件来加载完整历史
              // 注意：不要提前加载AI消息，等待WebSocket连接后统一加载
              setTimeout(() => {
                if (this.state.token) {
                  this.connectChatWebSocket();
                }
              }, 500);
            } else {
              console.log('Token is invalid, clearing login state');
              this.clearLoginState();
            }
          }).catch((err) => {
            console.error('Token verify network error:', err);
            this.clearLoginState();
          });
        }
      } catch (e) {
        console.error('Failed to restore login state:', e);
      }
    },

    // 验证 token 是否有效
    async verifyToken(token) {
      try {
        const response = await fetch(`${this.config.apiUrl}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        return response.ok;
      } catch (error) {
        console.error('Token verification failed:', error);
        return false;
      }
    },

    // 统一的 API 请求方法，处理 token 过期
    async apiRequest(url, options = {}) {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${this.state.token}`
        }
      });

      // 处理 token 过期
      if (response.status === 401) {
        console.error('Token expired, clearing login state');
        this.clearLoginState();
        this.state.isAuthenticated = false;
        this.createWidget(); // 重新渲染登录界面
        throw new Error('登录已过期，请重新登录');
      }

      return response;
    },

    // 清除登录状态
    clearLoginState() {
      // 关闭 WebSocket 连接
      if (this.state.ws) {
        this.state.ws.close();
        this.state.ws = null;
      }
      if (this.state.chatWs) {
        this.state.chatWs.close();
        this.state.chatWs = null;
      }
      // 清除心跳定时器
      if (this.state.wsHeartbeatInterval) {
        clearInterval(this.state.wsHeartbeatInterval);
        this.state.wsHeartbeatInterval = null;
      }
      if (this.state.chatWsHeartbeatInterval) {
        clearInterval(this.state.chatWsHeartbeatInterval);
        this.state.chatWsHeartbeatInterval = null;
      }

      try {
        localStorage.removeItem('widget_token');
        localStorage.removeItem('widget_user_id');
        localStorage.removeItem('widget_username');
      } catch (e) {
        console.error('Failed to clear localStorage:', e);
      }
      this.state.token = null;
      this.state.userId = null;
      this.state.isAuthenticated = false;
    },

    getStyles() {
      return `
        .ticket-widget-container {
          position: fixed;
          z-index: 999999;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .ticket-widget-bubble {
          position: fixed;
          bottom: 20px;
          right: 20px;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: #1890ff;
          color: white;
          border: none;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          transition: all 0.3s ease;
        }

        .ticket-widget-bubble:hover {
          transform: scale(1.1);
          box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }

        .ticket-widget-window {
          position: fixed;
          bottom: 90px;
          right: 20px;
          width: 380px;
          height: 500px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.15);
          display: none;
          flex-direction: column;
          overflow: hidden;
        }

        .ticket-widget-window.open {
          display: flex;
        }

        .ticket-widget-header {
          background: #1890ff;
          color: white;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .ticket-widget-title {
          font-size: 16px;
          font-weight: 500;
        }

        .ticket-widget-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ticket-widget-transfer {
          background: #fff;
          color: #1890ff;
          border: none;
          border-radius: 4px;
          padding: 4px 12px;
          font-size: 12px;
          cursor: pointer;
          font-weight: 500;
        }

        .ticket-widget-transfer:hover {
          background: #f0f0f0;
        }

        .ticket-widget-transfer:disabled {
          background: #d9d9d9;
          color: #999;
          cursor: not-allowed;
        }

        .ticket-widget-close {
          background: none;
          border: none;
          color: white;
          cursor: pointer;
          font-size: 20px;
          padding: 0;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .ticket-widget-body {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          background: #f5f5f5;
        }

        .ticket-widget-message {
          margin-bottom: 12px;
          display: flex;
          flex-direction: column;
        }

        .ticket-widget-message.user {
          align-items: flex-end;
        }

        .ticket-widget-message.agent {
          align-items: flex-start;
        }

        .ticket-widget-message-content {
          max-width: 80%;
          padding: 10px 14px;
          border-radius: 18px;
          word-wrap: break-word;
          white-space: pre-wrap;
          line-height: 1.5;
        }

        .ticket-widget-sender {
          font-size: 12px;
          color: #999;
          margin-bottom: 4px;
          padding-left: 4px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ticket-widget-message.user .ticket-widget-sender {
          padding-right: 4px;
          padding-left: 0;
          justify-content: flex-end;
        }

        .ticket-widget-message.system .ticket-widget-sender {
          justify-content: center;
        }

        .ticket-widget-time {
          font-size: 11px;
          color: #bbb;
          font-family: monospace;
        }

        .ticket-widget-message.user .ticket-widget-message-content {
          background: #1890ff;
          color: white;
          border-bottom-right-radius: 4px;
        }

        .ticket-widget-message.agent .ticket-widget-message-content {
          background: white;
          color: #333;
          border-bottom-left-radius: 4px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .ticket-widget-message.human {
          align-items: flex-start;
        }

        .ticket-widget-message.human .ticket-widget-message-content {
          background: #52c41a;
          color: white;
          border-bottom-left-radius: 4px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .ticket-widget-message.system {
          align-items: center;
        }

        .ticket-widget-message.system .ticket-widget-message-content {
          background: #f0f0f0;
          color: #666;
          font-size: 12px;
          padding: 6px 12px;
          border-radius: 12px;
          max-width: 90%;
          text-align: center;
        }

        .ticket-widget-footer {
          padding: 12px;
          background: white;
          border-top: 1px solid #e8e8e8;
          display: flex;
          gap: 8px;
        }

        .ticket-widget-input {
          flex: 1;
          border: 1px solid #d9d9d9;
          border-radius: 20px;
          padding: 8px 16px;
          font-size: 14px;
          outline: none;
          transition: border-color 0.3s;
        }

        .ticket-widget-input:focus {
          border-color: #1890ff;
        }

        .ticket-widget-send {
          background: #1890ff;
          color: white;
          border: none;
          border-radius: 50%;
          width: 36px;
          height: 36px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.3s;
        }

        .ticket-widget-send:hover {
          background: #40a9ff;
        }

        .ticket-widget-login {
          padding: 20px;
          text-align: center;
        }

        .ticket-widget-login input {
          width: 100%;
          padding: 10px;
          margin-bottom: 12px;
          border: 1px solid #d9d9d9;
          border-radius: 6px;
          font-size: 14px;
        }

        .ticket-widget-login button {
          width: 100%;
          padding: 10px;
          background: #1890ff;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }

        .ticket-widget-typing {
          display: flex;
          gap: 4px;
          padding: 8px 12px;
          background: white;
          border-radius: 18px;
          align-self: flex-start;
          margin-bottom: 12px;
        }

        .ticket-widget-typing-dot {
          width: 6px;
          height: 6px;
          background: #999;
          border-radius: 50%;
          animation: typing 1.4s infinite ease-in-out;
        }

        .ticket-widget-typing-dot:nth-child(2) {
          animation-delay: 0.2s;
        }

        .ticket-widget-typing-dot:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes typing {
          0%, 80%, 100% { transform: scale(0.6); }
          40% { transform: scale(1); }
        }
      `;
    },

    createWidget() {
      // 清空容器
      this.widgetContainer.innerHTML = '';

      // 创建气泡按钮
      const bubble = document.createElement('button');
      bubble.className = 'ticket-widget-bubble';
      bubble.innerHTML = '💬';
      bubble.id = 'ticket-widget-bubble';
      this.widgetContainer.appendChild(bubble);

      // 创建聊天窗口
      const window = document.createElement('div');
      window.className = 'ticket-widget-window';
      window.id = 'ticket-widget-window';
      window.innerHTML = `
        <div class="ticket-widget-header">
          <span class="ticket-widget-title">${this.config.title}</span>
          <div class="ticket-widget-actions">
            <button class="ticket-widget-transfer" id="ticket-widget-transfer" style="display: ${this.state.isAuthenticated ? 'block' : 'none'};">转人工</button>
            <button class="ticket-widget-close" id="ticket-widget-close">×</button>
          </div>
        </div>
        <div class="ticket-widget-body" id="ticket-widget-body">
          ${!this.state.isAuthenticated ? `
            <div class="ticket-widget-login" id="ticket-widget-login">
              <h3 style="margin-bottom: 16px;">请登录</h3>
              <input type="text" id="tw-username" placeholder="用户名" />
              <input type="password" id="tw-password" placeholder="密码" />
              <button id="tw-login-btn">登录</button>
            </div>
          ` : `
            <div class="ticket-widget-message agent">
              <div class="ticket-widget-message-content">${this.config.welcomeMessage.replace(/\n/g, '<br>')}</div>
            </div>
          `}
        </div>
        <div class="ticket-widget-footer" id="ticket-widget-footer" style="display: ${this.state.isAuthenticated ? 'flex' : 'none'};">
          <input type="text" class="ticket-widget-input" id="ticket-widget-input" placeholder="输入消息..." />
          <button class="ticket-widget-send" id="ticket-widget-send">➤</button>
        </div>
      `;
      this.widgetContainer.appendChild(window);
    },

    attachEventListeners() {
      // 使用 shadowRoot 查询元素
      const bubble = this.shadowRoot.getElementById('ticket-widget-bubble');
      const closeBtn = this.shadowRoot.getElementById('ticket-widget-close');
      const transferBtn = this.shadowRoot.getElementById('ticket-widget-transfer');
      const loginBtn = this.shadowRoot.getElementById('tw-login-btn');
      const sendBtn = this.shadowRoot.getElementById('ticket-widget-send');
      const input = this.shadowRoot.getElementById('ticket-widget-input');

      // 气泡按钮点击
      if (bubble) {
        bubble.addEventListener('click', () => this.toggleWindow());
      }

      // 关闭按钮
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.closeWindow());
      }

      // 转人工按钮
      if (transferBtn) {
        transferBtn.addEventListener('click', () => this.transferToHuman());
      }

      // 登录按钮
      if (loginBtn) {
        loginBtn.addEventListener('click', () => this.handleLogin());
      }

      // 发送按钮
      if (sendBtn) {
        sendBtn.addEventListener('click', () => this.sendMessage());
      }

      // 输入框回车
      if (input) {
        input.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            this.sendMessage();
          }
        });
      }
    },

    showChatBubble() {
      // 显示气泡（已经默认显示）
    },

    toggleWindow() {
      const window = this.shadowRoot.getElementById('ticket-widget-window');
      if (!window) return;
      window.classList.toggle('open');
      this.state.isOpen = window.classList.contains('open');
    },

    closeWindow() {
      const window = this.shadowRoot.getElementById('ticket-widget-window');
      if (!window) return;
      window.classList.remove('open');
      this.state.isOpen = false;
    },

    async handleLogin() {
      const username = this.shadowRoot.getElementById('tw-username').value;
      const password = this.shadowRoot.getElementById('tw-password').value;

      if (!username || !password) {
        alert('请输入用户名和密码');
        return;
      }

      try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${this.config.apiUrl}/auth/login`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error('Login failed');
        }

        const data = await response.json();
        this.state.token = data.access_token;
        this.state.isAuthenticated = true;

        // 获取用户信息
        const userResponse = await fetch(`${this.config.apiUrl}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${data.access_token}`
          }
        });

        let displayName = '';
        if (userResponse.ok) {
          const userData = await userResponse.json();
          this.state.userId = userData.id;
          displayName = userData.username || userData.full_name || '';
        }

        // 保存登录状态到 localStorage
        localStorage.setItem('widget_token', data.access_token);
        localStorage.setItem('widget_user_id', this.state.userId || '');
        localStorage.setItem('widget_username', displayName);
        console.log('Login state saved to localStorage');

        // 重新渲染窗口
        this.refreshWindow();
        this.attachEventListeners();
        // 加载AI聊天记录
        await this.loadAndDisplayAIMessages();
        this.connectWebSocket();
        // 连接聊天WebSocket（用于接收客服消息）
        setTimeout(() => {
          if (this.state.token) {
            this.connectChatWebSocket();
          }
        }, 500);

      } catch (error) {
        alert('登录失败，请检查用户名和密码');
      }
    },

    refreshWindow() {
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      const footer = this.shadowRoot.getElementById('ticket-widget-footer');
      const transferBtn = this.shadowRoot.getElementById('ticket-widget-transfer');

      body.innerHTML = `
        <div class="ticket-widget-message agent">
          <div class="ticket-widget-message-content">${this.config.welcomeMessage.replace(/\n/g, '<br>')}</div>
        </div>
      `;
      footer.style.display = 'flex';

      // 重置转人工按钮
      if (transferBtn) {
        transferBtn.style.display = 'block';
        transferBtn.disabled = false;
        transferBtn.textContent = '转人工';
      }

      // 重置聊天模式
      this.state.chatMode = 'ai';
      this.state.chatSessionId = null;
      this.state.isWaitingForAgent = false;
      this.state.historyLoadedForSession = null; // 重置历史加载标志
      this.state.messages = []; // 清空AI对话历史

      // 关闭聊天WebSocket
      if (this.state.chatWs) {
        this.state.chatWs.close();
        this.state.chatWs = null;
      }
    },

    async sendMessage() {
      const input = this.shadowRoot.getElementById('ticket-widget-input');
      const message = input.value.trim();

      if (!message) return;

      // 添加用户消息
      this.addMessage(message, 'user');
      input.value = '';

      // 检查是否是转人工关键词
      if (this.state.chatMode === 'ai' && /转人工|人工客服|人工服务|找客服/.test(message)) {
        this.transferToHuman();
        return;
      }

      // 人工模式：通过WebSocket发送消息
      if (this.state.chatMode === 'human' && this.state.chatWs) {
        this.state.chatWs.send(JSON.stringify({
          type: 'chat_message',
          session_id: this.state.chatSessionId,
          content: message
        }));
        return;
      }

      // 显示正在输入
      this.showTyping();

      // 保存用户消息到数据库（AI聊天记录）
      try {
        await this.saveAIMessageToDatabase('customer', message);
      } catch (e) {
        console.error('Failed to save AI message:', e);
      }

      try {
        // 调用智能体API
        const response = await this.apiRequest(`${this.config.apiUrl}/chat/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: message
          })
        });

        if (response.ok) {
          const data = await response.json();
          this.hideTyping();
          // 显示智能体回复（AI回复中已包含工单信息，无需额外显示卡片）
          this.addMessage(data.response, 'agent');
          // 保存AI回复到数据库
          this.saveAIMessageToDatabase('ai', data.response);
        } else {
          throw new Error('Failed to get response');
        }
      } catch (error) {
        this.hideTyping();
        if (error.message.includes('登录已过期')) {
          this.addMessage('登录已过期，请重新登录。', 'system');
        } else {
          this.addMessage('抱歉，服务暂时不可用，请稍后重试。', 'agent');
        }
        console.error('Chat error:', error);
      }
    },

    addMessage(content, type, senderName = null) {
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      if (!body) return;
      const messageDiv = document.createElement('div');
      messageDiv.className = `ticket-widget-message ${type}`;

      // 转义HTML (保留换行符，使用white-space: pre-wrap显示)
      const formattedContent = this.escapeHtml(content);

      // 获取当前时间 (统一格式)
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      const milliseconds = String(now.getMilliseconds()).padStart(3, '0');
      const timeStr = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;

      // 如果有发送者名称且不是用户自己，显示发送者
      let senderHtml = '';
      if (senderName && type !== 'user') {
        senderHtml = `<div class="ticket-widget-sender"><span>${this.escapeHtml(senderName)}</span><span class="ticket-widget-time">${timeStr}</span></div>`;
      } else if (type === 'user') {
        // 用户消息只显示时间（右侧）
        senderHtml = `<div class="ticket-widget-sender"><span class="ticket-widget-time">${timeStr}</span></div>`;
      }

      messageDiv.innerHTML = `
        ${senderHtml}
        <div class="ticket-widget-message-content">${formattedContent}</div>
      `;
      body.appendChild(messageDiv);
      body.scrollTop = body.scrollHeight;

      // 保存消息到状态（用于转人工时发送历史记录）
      // 只保存用户和AI的消息，不保存系统消息和人工客服消息
      if (type === 'user') {
        this.state.messages.push({
          role: 'customer',
          content: content,
          timestamp: Date.now()
        });
        console.log('Saved user message to state, total messages:', this.state.messages.length);
        // 限制存储的消息数量，最多保留最近50条
        if (this.state.messages.length > 50) {
          this.state.messages = this.state.messages.slice(-50);
        }
      } else if (type === 'agent' && this.state.chatMode === 'ai') {
        // 只在AI模式下保存AI回复，人工模式下不保存（人工消息已在服务器保存）
        this.state.messages.push({
          role: 'ai',
          content: content,
          timestamp: Date.now()
        });
        console.log('Saved AI message to state, total messages:', this.state.messages.length);
        // 限制存储的消息数量，最多保留最近50条
        if (this.state.messages.length > 50) {
          this.state.messages = this.state.messages.slice(-50);
        }
      }
      console.log('Current chatMode:', this.state.chatMode, 'message type:', type);
    },

    // 保存AI消息到数据库
    async saveAIMessageToDatabase(role, content) {
      try {
        if (!this.state.token) return;
        const response = await this.apiRequest(`${this.config.apiUrl}/chat-service/ai-messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            role: role,
            content: content
          })
        });
        if (response.ok) {
          console.log('Saved AI message to database:', role);
        }
      } catch (error) {
        console.error('Failed to save AI message:', error);
      }
    },

    // 从数据库加载AI消息（支持分页）
    async loadAIMessagesFromDatabase(page = 1) {
      try {
        if (!this.state.token) {
          console.log('No token, skipping load AI messages');
          return { items: [], total: 0, has_more: false };
        }
        console.log('Loading AI messages from database, page:', page);
        const response = await this.apiRequest(
          `${this.config.apiUrl}/chat-service/ai-messages?page=${page}&page_size=10`
        );
        console.log('AI messages API response:', response.status);
        if (response.ok) {
          const data = await response.json();
          console.log('Loaded AI messages from database:', data.items?.length || 0, 'messages, total:', data.total);
          return data;
        } else {
          console.error('Failed to load AI messages:', response.status);
        }
      } catch (error) {
        console.error('Failed to load AI messages:', error);
      }
      return { items: [], total: 0, has_more: false };
    },

    // 加载并显示AI聊天记录（分页加载）
    async loadAndDisplayAIMessages() {
      console.log('loadAndDisplayAIMessages called');

      // 检查 body 元素是否存在
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      console.log('Body element:', body);
      if (!body) {
        console.error('Body element not found, delaying...');
        setTimeout(() => this.loadAndDisplayAIMessages(), 500);
        return;
      }

      // 先获取第一页以获取总数
      const firstData = await this.loadAIMessagesFromDatabase(1);
      if (!firstData.items || firstData.items.length === 0) {
        console.log('No AI messages to display');
        return;
      }

      const totalPages = Math.ceil(firstData.total / 10);
      console.log('Total pages:', totalPages, 'total messages:', firstData.total);

      // 清空欢迎消息
      body.innerHTML = '';
      this.state.messages = [];

      // 如果只有一页，直接显示
      if (totalPages <= 1) {
        this.renderAIMessages(firstData.items);
        this.state.aiHistoryPage = 1;
        this.state.aiHistoryHasMore = false;
      } else {
        // 加载最后一页（最新的消息）
        const lastData = await this.loadAIMessagesFromDatabase(totalPages);
        this.renderAIMessages(lastData.items);
        this.state.aiHistoryPage = totalPages;
        this.state.aiHistoryHasMore = totalPages > 1;

        // 添加滚动监听，滚动到顶部加载更早消息
        this.attachAIHistoryScrollListener(body);
      }

      // 滚动到底部显示最新消息
      body.scrollTop = body.scrollHeight;
    },

    // 渲染AI历史消息
    // 统一渲染规则：
    // - 客户消息: role='customer' -> type='user'
    // - AI消息: role='ai' -> type='agent', senderName='AI助手'
    renderAIMessages(messages) {
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      messages.forEach(msg => {
        const type = msg.role === 'customer' ? 'user' : 'agent';
        const senderName = msg.role === 'ai' ? 'AI助手' : null;
        this.displayMessage(msg.content, type, senderName, msg.created_at);
        this.state.messages.push({
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at).getTime()
        });
      });
      console.log('Rendered', messages.length, 'AI messages');
    },

    // 添加AI历史消息滚动监听
    attachAIHistoryScrollListener(body) {
      if (body._aiScrollListenerAttached) return;
      body._aiScrollListenerAttached = true;

      body.addEventListener('scroll', async () => {
        // 当滚动到顶部且还有更多历史记录时
        if (body.scrollTop < 50 && this.state.aiHistoryHasMore && !this.state.isLoadingAIHistory) {
          const nextPage = this.state.aiHistoryPage - 1;
          if (nextPage >= 1) {
            this.state.isLoadingAIHistory = true;
            this.showHistoryLoadingIndicator(true);

            const data = await this.loadAIMessagesFromDatabase(nextPage);
            if (data.items && data.items.length > 0) {
              // 在顶部插入更早的消息
              const oldScrollHeight = body.scrollHeight;
              const fragment = document.createDocumentFragment();

              data.items.forEach(msg => {
                const type = msg.role === 'customer' ? 'user' : 'agent';
                const senderName = msg.role === 'ai' ? 'AI助手' : null;
                const timeStr = this.formatMessageTime(msg.created_at);

                const messageDiv = document.createElement('div');
                messageDiv.className = `ticket-widget-message ${type}`;
                // 转义HTML (保留换行符，使用white-space: pre-wrap显示)
                const formattedContent = this.escapeHtml(msg.content);
                let senderHtml = '';
                if (senderName && type !== 'user') {
                  senderHtml = `<div class="ticket-widget-sender"><span>${this.escapeHtml(senderName)}</span><span class="ticket-widget-time">${timeStr}</span></div>`;
                } else if (type === 'user') {
                  senderHtml = `<div class="ticket-widget-sender"><span class="ticket-widget-time">${timeStr}</span></div>`;
                }
                messageDiv.innerHTML = `
                  ${senderHtml}
                  <div class="ticket-widget-message-content">${formattedContent}</div>
                `;
                fragment.appendChild(messageDiv);
              });

              body.insertBefore(fragment, body.firstChild);

              // 保持滚动位置
              const newScrollHeight = body.scrollHeight;
              body.scrollTop = newScrollHeight - oldScrollHeight + 50;

              this.state.aiHistoryPage = nextPage;
              this.state.aiHistoryHasMore = nextPage > 1;
            }

            this.showHistoryLoadingIndicator(false);
            this.state.isLoadingAIHistory = false;
          }
        }
      });
    },

    // 仅显示消息（不保存到数据库）
    displayMessage(content, type, senderName = null, createdAt = null) {
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      const messageDiv = document.createElement('div');
      messageDiv.className = `ticket-widget-message ${type}`;

      // 转义HTML (保留换行符，使用white-space: pre-wrap显示)
      const formattedContent = this.escapeHtml(content);

      // 获取时间
      const timeStr = createdAt
        ? this.formatMessageTime(createdAt)
        : this.formatMessageTime(new Date().toISOString());

      let senderHtml = '';
      if (senderName && type !== 'user') {
        senderHtml = `<div class="ticket-widget-sender"><span>${this.escapeHtml(senderName)}</span><span class="ticket-widget-time">${timeStr}</span></div>`;
      } else if (type === 'user') {
        // 用户消息只显示时间（右侧）
        senderHtml = `<div class="ticket-widget-sender"><span class="ticket-widget-time">${timeStr}</span></div>`;
      }

      messageDiv.innerHTML = `
        ${senderHtml}
        <div class="ticket-widget-message-content">${formattedContent}</div>
      `;
      body.appendChild(messageDiv);
    },

    // 显示/隐藏历史消息加载提示
    showHistoryLoadingIndicator(show) {
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      let indicator = this.shadowRoot.getElementById('history-loading-indicator');

      if (show) {
        if (!indicator) {
          indicator = document.createElement('div');
          indicator.id = 'history-loading-indicator';
          indicator.className = 'ticket-widget-history-loading';
          indicator.innerHTML = `
            <div class="ticket-widget-loading-spinner"></div>
            <span>加载更多历史消息...</span>
          `;
          indicator.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            color: #999;
            font-size: 12px;
            gap: 8px;
          `;
        }
        if (body.firstChild) {
          body.insertBefore(indicator, body.firstChild);
        } else {
          body.appendChild(indicator);
        }
      } else if (indicator) {
        indicator.remove();
      }
    },

    // 计算总页数
    calculateTotalPages(total, pageSize) {
      return Math.ceil(total / pageSize);
    },

    // 加载聊天历史消息（支持分页）
    // mode: 'init' - 首次加载（从最后一页开始），'older' - 加载更早的消息，'newer' - 加载更新的消息
    // includeAIHistory: 是否包含AI聊天历史，默认true。在已显示AI消息的情况下设置为false
    async loadChatHistory(sessionId, mode = 'init', page = null, includeAIHistory = true) {
      console.log('loadChatHistory called:', 'sessionId=', sessionId, 'mode=', mode, 'page=', page, 'includeAI=', includeAIHistory);

      // 防止重复加载
      if (this.state.isLoadingHistory) {
        console.log('Already loading history, skipping');
        return;
      }

      // 防止同一会话重复加载历史（init模式下且包含AI历史时）
      if (mode === 'init' && includeAIHistory && this.state.historyLoadedForSession === sessionId) {
        console.log('History already loaded for session', sessionId, ', skipping');
        return;
      }

      try {
        this.state.isLoadingHistory = true;

        let targetPage = page;

        // 如果是首次加载，加载所有消息（不分页）
        if (mode === 'init') {
          // 获取第一页以获取总数量
          const firstResponse = await this.apiRequest(
            `${this.config.apiUrl}/chat-service/sessions/${sessionId}/messages?page=1&page_size=10&include_ai_history=${includeAIHistory}`
          );
          if (!firstResponse.ok) {
            console.error('Failed to load chat history:', firstResponse.status);
            return;
          }
          const firstData = await firstResponse.json();
          const totalPages = this.calculateTotalPages(firstData.total, 10);
          const maxInitPages = 10;

          console.log('Init load: total=', firstData.total, 'pages=', totalPages);

          // 如果只有一页，直接渲染
          if (totalPages <= 1) {
            this.renderChatMessages(firstData.items, 'init', sessionId);
            this.state.chatHistoryPage = 1;
            this.state.chatHistoryHasMore = false;
            return;
          }

          // 有多页数据，限制初始化最多加载最近 maxInitPages 页（避免内存与请求爆炸）
          const allMessages = [];
          const startPage = Math.max(1, totalPages - maxInitPages + 1);

          for (let p = startPage; p <= totalPages; p++) {
            let pageData;
            if (p === 1) {
              pageData = firstData;
            } else {
              console.log('Loading page', p, 'of', totalPages);
              const resp = await this.apiRequest(
                `${this.config.apiUrl}/chat-service/sessions/${sessionId}/messages?page=${p}&page_size=10&include_ai_history=${includeAIHistory}`
              );
              if (resp.ok) {
                pageData = await resp.json();
                console.log('Page', p, 'loaded:', pageData.items?.length || 0, 'messages');
              } else {
                console.error('Failed to load page', p);
                continue;
              }
            }
            allMessages.push(...(pageData.items || []));
          }

          console.log('Loaded messages:', allMessages.length, 'of', firstData.total);
          this.state.chatHistoryPage = startPage;
          this.state.chatHistoryHasMore = startPage > 1;
          this.state.historyLoadedForSession = sessionId; // 标记已加载
          this.renderChatMessages(allMessages, 'init', sessionId);
          return;
        }

        // 显示加载提示
        if (mode === 'older') {
          this.showHistoryLoadingIndicator(true);
        }

        console.log('Loading chat history for session:', sessionId, 'page:', targetPage, 'mode:', mode);

        const response = await this.apiRequest(
          `${this.config.apiUrl}/chat-service/sessions/${sessionId}/messages?page=${targetPage}&page_size=10&include_ai_history=${includeAIHistory}`
        );

        if (!response.ok) {
          console.error('Failed to load chat history:', response.status);
          return;
        }

        const data = await response.json();
        console.log('Loaded chat history:', data);

        // 更新分页状态
        this.state.chatHistoryPage = targetPage;
        this.state.chatHistoryHasMore = targetPage > 1;

        this.renderChatMessages(data.items, mode, sessionId);
      } catch (error) {
        console.error('Error loading chat history:', error);
      } finally {
        this.state.isLoadingHistory = false;
        // 隐藏加载提示
        this.showHistoryLoadingIndicator(false);
      }
    },

    // 格式化时间显示 (统一格式: yyyy-MM-dd HH:mm:ss.SSS)
    formatMessageTime(createdAt) {
      const date = new Date(createdAt);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');
      const milliseconds = String(date.getMilliseconds()).padStart(3, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;
    },

    // 渲染聊天消息
    // 统一渲染规则：
    // | sender_type | sender_id | 显示名称 |
    // |-------------|-----------|----------|
    // | ai          | NULL      | AI助手   |
    // | customer    | 有值      | 客户     |
    // | agent       | 有值      | 客服(名) |
    // | system      | NULL/有值 | 系统     |
    renderChatMessages(messages, mode, sessionId) {
      console.log('renderChatMessages called:', messages.length, 'messages, mode:', mode);

      if (!messages || messages.length === 0) {
        console.log('No messages to render');
        return;
      }

      const body = this.shadowRoot.getElementById('ticket-widget-body');
      console.log('Body element found:', !!body);

      // 记录当前滚动高度（用于加载更早历史时保持滚动位置）
      const oldScrollHeight = body.scrollHeight;
      const oldScrollTop = body.scrollTop;

      // 如果是初始化模式，清空整个消息区域
      // 因为现在是一次性加载所有消息（AI+客服），不需要保留任何现有消息
      if (mode === 'init') {
        body.innerHTML = '';
      }

      // 创建消息元素数组
      const messageElements = [];
      messages.forEach(msg => {
        let msgType;
        let senderName = null;

        // 统一渲染规则
        switch (msg.sender_type) {
          case 'ai':
            msgType = 'agent';
            senderName = 'AI助手';
            break;
          case 'customer':
            msgType = 'user';
            // 客户消息不显示发送者名称（自己发的）
            break;
          case 'agent':
            msgType = 'human';
            senderName = msg.sender?.name ? `客服(${msg.sender.name})` : '客服';
            break;
          case 'system':
            msgType = 'system';
            senderName = '系统';
            break;
          default:
            msgType = 'system';
            senderName = msg.sender?.name || '系统';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `ticket-widget-message ${msgType}`;
        messageDiv.dataset.messageId = msg.id;

        // 转义HTML (保留换行符，使用white-space: pre-wrap显示)
        const formattedContent = this.escapeHtml(msg.content);
        const timeStr = this.formatMessageTime(msg.created_at);

        let senderHtml = '';
        if (senderName && msgType !== 'user') {
          senderHtml = `<div class="ticket-widget-sender"><span>${this.escapeHtml(senderName)}</span><span class="ticket-widget-time">${timeStr}</span></div>`;
        } else if (msgType === 'user') {
          // 用户消息只显示时间（在右侧）
          senderHtml = `<div class="ticket-widget-sender"><span class="ticket-widget-time">${timeStr}</span></div>`;
        }

        messageDiv.innerHTML = `
          ${senderHtml}
          <div class="ticket-widget-message-content">${formattedContent}</div>
        `;
        messageElements.push(messageDiv);
      });

      if (mode === 'older') {
        // 在顶部插入消息（加载更早的历史）
        messageElements.reverse().forEach(el => { // 反转顺序，因为API返回的是正序
          body.insertBefore(el, body.firstChild);
        });
        // 保持滚动位置
        const newScrollHeight = body.scrollHeight;
        body.scrollTop = newScrollHeight - oldScrollHeight + oldScrollTop;
      } else {
        // 在底部追加消息（首次加载或加载更新消息）
        messageElements.forEach(el => {
          body.appendChild(el);
        });
        // 滚动到底部
        body.scrollTop = body.scrollHeight;
      }

      // 如果是初始化模式，添加滚动监听
      if (mode === 'init' && !body._hasScrollListener) {
        this.attachHistoryScrollListener(body, sessionId);
      }
    },

    // 添加历史消息滚动监听
    attachHistoryScrollListener(body, sessionId) {
      body._hasScrollListener = true;

      body.addEventListener('scroll', () => {
        // 当滚动到顶部且还有更多历史记录时，加载更早的消息（上一页）
        if (body.scrollTop < 50 && this.state.chatHistoryHasMore && !this.state.isLoadingHistory) {
          const nextPage = this.state.chatHistoryPage - 1;
          if (nextPage >= 1) {
            this.loadChatHistory(sessionId, 'older', nextPage);
          }
        }
      });

      console.log('Attached scroll listener for history loading');
    },

    showTyping() {
      const body = this.shadowRoot.getElementById('ticket-widget-body');
      const typingDiv = document.createElement('div');
      typingDiv.className = 'ticket-widget-typing';
      typingDiv.id = 'ticket-widget-typing';
      typingDiv.innerHTML = `
        <div class="ticket-widget-typing-dot"></div>
        <div class="ticket-widget-typing-dot"></div>
        <div class="ticket-widget-typing-dot"></div>
      `;
      body.appendChild(typingDiv);
      body.scrollTop = body.scrollHeight;
    },

    hideTyping() {
      const typing = this.shadowRoot.getElementById('ticket-widget-typing');
      if (typing) {
        typing.remove();
      }
    },

    connectWebSocket() {
      if (!this.config.websocketUrl || !this.state.token) return;

      // 如果已有连接且处于 OPEN 或 CONNECTING 状态，不再重复连接
      if (this.state.ws && (this.state.ws.readyState === WebSocket.OPEN || this.state.ws.readyState === WebSocket.CONNECTING)) {
        console.log('WebSocket already connected or connecting, skipping');
        return;
      }

      // 清理已有的心跳定时器
      if (this.state.wsHeartbeatInterval) {
        clearInterval(this.state.wsHeartbeatInterval);
        this.state.wsHeartbeatInterval = null;
      }
      if (this.state.wsHeartbeatTimeout) {
        clearTimeout(this.state.wsHeartbeatTimeout);
        this.state.wsHeartbeatTimeout = null;
      }

      try {
        this.state.ws = new WebSocket(`${this.config.websocketUrl}?token=${this.state.token}`);

        // 记录上次收到 pong 的时间
        this.state.lastPongTime = Date.now();

        this.state.ws.onopen = () => {
          console.log('WebSocket connected');
          // 启动心跳
          this._startHeartbeat();
        };

        this.state.ws.onmessage = (event) => {
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (e) {
            console.error('Invalid WebSocket JSON:', event.data);
            return;
          }
          // 处理 pong 响应
          if (data.type === 'pong') {
            this.state.lastPongTime = Date.now();
            return;
          }
          this.handleWebSocketMessage(data);
        };

        this.state.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        this.state.ws.onclose = (event) => {
          console.log('WebSocket closed', event.code, event.reason);
          // 清理心跳
          this._stopHeartbeat();
          // 认证失败（token 过期/无效）
          if (event.code === 4001) {
            console.warn('WebSocket authentication failed, logging out');
            this.clearLoginState();
            this.state.isAuthenticated = false;
            this.createWidget();
            this.attachEventListeners();
            return;
          }
          // 尝试重连
          setTimeout(() => this.connectWebSocket(), 5000);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
      }
    },

    // 启动心跳
    _startHeartbeat() {
      // 每 30 秒发送一次 ping
      this.state.wsHeartbeatInterval = setInterval(() => {
        if (this.state.ws && this.state.ws.readyState === WebSocket.OPEN) {
          this.state.ws.send(JSON.stringify({ type: 'ping' }));

          // 检查是否在 60 秒内收到过 pong
          const timeSinceLastPong = Date.now() - this.state.lastPongTime;
          if (timeSinceLastPong > 60000) {
            console.warn('WebSocket heartbeat timeout, reconnecting...');
            this.state.ws.close();
          }
        }
      }, 30000);
    },

    // 停止心跳
    _stopHeartbeat() {
      if (this.state.wsHeartbeatInterval) {
        clearInterval(this.state.wsHeartbeatInterval);
        this.state.wsHeartbeatInterval = null;
      }
    },

    handleWebSocketMessage(data) {
      switch (data.type) {
        case 'ticket_status_update':
          this.addMessage(`工单 ${data.ticket_id} 状态已更新为 ${data.status}`, 'agent');
          break;
        case 'new_message':
          this.addMessage(data.message.content, 'agent');
          break;
      }
    },

    escapeHtml(text) {
      if (typeof text !== 'string') return String(text);
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    },

    // 转人工服务
    async transferToHuman() {
      if (this.state.chatMode === 'human') {
        this.addMessage('您已经在人工服务中', 'system');
        return;
      }

      const transferBtn = this.shadowRoot.getElementById('ticket-widget-transfer');
      if (transferBtn) {
        transferBtn.disabled = true;
        transferBtn.textContent = '连接中...';
      }

      this.addMessage('正在为您转接人工客服，请稍候...', 'system');

      try {
        // 准备AI对话历史（过滤掉空消息，限制数量）
        console.log('Current messages in state:', this.state.messages);
        const aiConversationHistory = this.state.messages
          .filter(msg => msg.content && msg.content.trim())
          .slice(-20); // 最多发送最近20条

        console.log('Transferring to human with conversation history:', aiConversationHistory.length, 'messages');
        console.log('Conversation history content:', JSON.stringify(aiConversationHistory));

        const response = await this.apiRequest(`${this.config.apiUrl}/chat-service/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            request_type: 'general',
            message: '客户请求转人工',
            ai_conversation_history: aiConversationHistory
          })
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error('Transfer to human API error:', response.status, errorData);
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('Transfer to human response:', data);

        if (data.status === 'connected') {
          this.state.chatMode = 'human';
          this.state.chatSessionId = data.session_id;
          this.state.isWaitingForAgent = false;

          // 隐藏转人工按钮
          if (transferBtn) {
            transferBtn.style.display = 'none';
          }

          // 关闭旧的聊天WebSocket连接（如果有）
          if (this.state.chatWs) {
            this.state.chatWs.close();
            this.state.chatWs = null;
          }
          // 连接聊天WebSocket（连接后会收到 session_assigned 事件，然后加载历史消息）
          this.connectChatWebSocket(data.session_id);
        } else {
          this.state.chatMode = 'human';
          this.state.chatSessionId = data.session_id;
          this.state.isWaitingForAgent = true;
          const position = data.queue_position || '?';
          this.addMessage(`当前排队位置：第${position}位，请稍候...`, 'system');

          if (transferBtn) {
            transferBtn.textContent = '排队中...';
          }

          // 关闭旧的聊天WebSocket连接（如果有）
          if (this.state.chatWs) {
            this.state.chatWs.close();
            this.state.chatWs = null;
          }
          // 连接聊天WebSocket等待接入
          this.connectChatWebSocket(data.session_id);
        }
      } catch (error) {
        console.error('Transfer to human failed:', error);
        this.addMessage('转接失败，请稍后重试', 'system');
        if (transferBtn) {
          transferBtn.disabled = false;
          transferBtn.textContent = '转人工';
        }
      }
    },

    // 连接聊天WebSocket
    connectChatWebSocket(sessionId) {
      // 如果已有连接且处于 OPEN 或 CONNECTING 状态，不再重复连接
      if (this.state.chatWs && (this.state.chatWs.readyState === WebSocket.OPEN || this.state.chatWs.readyState === WebSocket.CONNECTING)) {
        console.log('Chat WebSocket already connected or connecting, skipping');
        return;
      }

      // 清理已有的聊天心跳定时器
      if (this.state.chatWsHeartbeatInterval) {
        clearInterval(this.state.chatWsHeartbeatInterval);
        this.state.chatWsHeartbeatInterval = null;
      }

      // WebSocket URL: 如果 websocketUrl 已经是 ws://host/ws，则添加 /chat
      let baseUrl = this.config.websocketUrl;
      if (baseUrl.endsWith('/ws')) {
        baseUrl = baseUrl + '/chat';
      }
      const wsUrl = `${baseUrl}?token=${this.state.token}`;
      console.log('Connecting to chat WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);
      this.state.chatWs = ws;

      // 记录上次收到 pong 的时间
      let lastPongTime = Date.now();

      ws.onopen = () => {
        console.log('Chat WebSocket connected');
        // 启动心跳
        this.state.chatWsHeartbeatInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));

            // 检查是否在 60 秒内收到过 pong
            const timeSinceLastPong = Date.now() - lastPongTime;
            if (timeSinceLastPong > 60000) {
              console.warn('Chat WebSocket heartbeat timeout, reconnecting...');
              ws.close();
            }
          }
        }, 30000);

        // 如果有 sessionId，主动加入会话
        // 注意：加载历史消息在收到 session_rejoined 或 session_assigned 后处理
        if (sessionId) {
          ws.send(JSON.stringify({
            type: 'join_session',
            session_id: sessionId,
            role: 'customer'
          }));
          // 不在这里加载历史消息，等待服务器确认后再加载
        } else {
          console.log('No sessionId provided, waiting for session_rejoined from server');
        }
      };

      ws.onmessage = (event) => {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch (e) {
          console.error('Invalid Chat WebSocket JSON:', event.data);
          return;
        }
        // 处理 pong 响应
        if (data.type === 'pong') {
          lastPongTime = Date.now();
          return;
        }
        console.log('Widget received WebSocket message:', data);
        this.handleChatWebSocketMessage(data);
      };

      ws.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('Chat WebSocket closed', event.code, event.reason);
        // 清理心跳
        if (this.state.chatWsHeartbeatInterval) {
          clearInterval(this.state.chatWsHeartbeatInterval);
          this.state.chatWsHeartbeatInterval = null;
        }
        // 认证失败时不做重连，由主 WebSocket 的 onclose 统一处理登出
        if (event.code === 4001) {
          return;
        }
      };
    },

    // 处理聊天WebSocket消息
    handleChatWebSocketMessage(data) {
      console.log('handleChatWebSocketMessage:', data);
      switch (data.type) {
        case 'new_message':
          console.log('Received new_message:', data.message);
          // 根据发送者类型显示不同样式
          // agent 发送的消息显示为 'human' (左侧)，其他显示为 'user' (右侧)
          let msgType;
          let senderName = null;
          if (data.message.sender_type === 'agent') {
            msgType = 'human';  // 客服消息显示在左侧
            senderName = data.message.sender?.name || '客服';
          } else if (data.message.sender_type === 'customer') {
            msgType = 'user';   // 客户自己的消息已经在本地显示，这里跳过
            console.log('Skipping customer message (already displayed locally)');
            return;  // 跳过客户自己发的消息，因为已经在发送时本地显示了
          } else {
            msgType = 'human';  // 系统消息或其他
            senderName = data.message.sender?.name || '系统';
          }
          this.addMessage(data.message.content, msgType, senderName);
          break;
        case 'session_assigned':
          this.state.isWaitingForAgent = false;
          this.state.chatSessionId = data.session_id;
          const agentName = data.agent?.name || '客服';

          // 隐藏转人工按钮
          const transferBtn = this.shadowRoot.getElementById('ticket-widget-transfer');
          if (transferBtn) {
            transferBtn.style.display = 'none';
          }

          // 加载历史消息（包含AI聊天历史）
          // 一次性加载所有消息（AI+客服），按时间排序
          this.loadChatHistory(data.session_id, 'init', null, true);
          break;
        case 'session_rejoined':
          // 重新加入之前的会话
          console.log('Rejoined session:', data.session_id, 'as', data.role, 'status:', data.status);

          // 注意：已关闭的会话应该走 session_history，这里处理进行中的会话
          if (data.status === 'closed') {
            console.warn('Unexpected: session_rejoined with closed status, switching to AI mode');
            this.state.chatMode = 'ai';
            this.state.chatSessionId = null;
            this.state.isWaitingForAgent = false;
            this.state.historyLoadedForSession = null; // 重置历史加载标志
            this.state.messages = []; // 清空AI对话历史
            // 清空消息区域并显示提示
            const body = this.shadowRoot.getElementById('ticket-widget-body');
            body.innerHTML = '';
            this.addMessage(data.message || '会话已结束，已回到AI模式', 'system');
            // 一次性加载所有历史消息（AI+客服）
            this.loadChatHistory(data.session_id, 'init', null, true);
            // 恢复输入框
            const closedInput = this.shadowRoot.getElementById('ticket-widget-input');
            const closedSendBtn = this.shadowRoot.getElementById('ticket-widget-send');
            if (closedInput) {
              closedInput.disabled = false;
              closedInput.placeholder = '输入消息...';
            }
            if (closedSendBtn) {
              closedSendBtn.disabled = false;
            }
            break;
          }

          // 会话进行中，正常恢复
          this.state.chatMode = 'human';
          this.state.chatSessionId = data.session_id;
          this.state.isWaitingForAgent = false;

          // 隐藏转人工按钮
          const transferBtnRejoin = this.shadowRoot.getElementById('ticket-widget-transfer');
          if (transferBtnRejoin) {
            transferBtnRejoin.style.display = 'none';
          }

          // 一次性加载所有消息（AI历史 + 客服会话消息，按时间排序）
          // 使用 include_ai_history=true 让后端返回合并后的完整历史
          this.loadChatHistory(data.session_id, 'init', null, true);

          // 确保 WebSocket 连接已建立，加入会话
          if (this.state.chatWs && this.state.chatWs.readyState === WebSocket.OPEN) {
            this.state.chatWs.send(JSON.stringify({
              type: 'join_session',
              session_id: data.session_id,
              role: data.role
            }));
          } else {
            // 如果聊天 WebSocket 未连接，重新连接
            this.connectChatWebSocket(data.session_id);
          }
          break;
        case 'session_history':
          // 已关闭会话的历史记录 - 回到AI模式
          console.log('Session history, switching back to AI mode:', data.session_id);
          this.state.chatMode = 'ai'; // 回到AI模式
          this.state.chatSessionId = null; // 不保存会话ID
          this.state.isWaitingForAgent = false;
          this.state.historyLoadedForSession = null; // 重置历史加载标志
          this.state.messages = []; // 清空AI对话历史

          // 添加历史记录提示（注意：在加载历史之前添加，这样历史消息会显示在提示下方）
          const body = this.shadowRoot.getElementById('ticket-widget-body');
          body.innerHTML = ''; // 先清空
          this.addMessage('━━━━━━━━━━━━━━━━━━━━', 'system');
          this.addMessage(data.message || '会话已结束，以下是历史记录', 'system');
          this.addMessage('━━━━━━━━━━━━━━━━━━━━', 'system');

          // 一次性加载所有历史消息（AI+客服）
          this.loadChatHistory(data.session_id, 'init', null, true);

          // 恢复AI模式提示
          setTimeout(() => {
            this.addMessage('您可以继续向我提问~', 'system');
          }, 500);

          // 恢复输入框和发送按钮
          const historyInput = this.shadowRoot.getElementById('ticket-widget-input');
          const historySendBtn = this.shadowRoot.getElementById('ticket-widget-send');
          if (historyInput) {
            historyInput.disabled = false;
            historyInput.placeholder = '输入消息...';
            historyInput.style.backgroundColor = '';
          }
          if (historySendBtn) {
            historySendBtn.disabled = false;
            historySendBtn.style.opacity = '1';
          }

          // 显示转人工按钮
          const historyTransferBtn = this.shadowRoot.getElementById('ticket-widget-transfer');
          if (historyTransferBtn) {
            historyTransferBtn.style.display = 'block';
            historyTransferBtn.disabled = false;
            historyTransferBtn.textContent = '转人工';
          }
          break;
        case 'session_closed':
          this.addMessage(data.message || '会话已结束', 'system');
          // 重置聊天状态
          this.state.chatMode = 'ai';
          this.state.chatSessionId = null;
          this.state.historyLoadedForSession = null; // 重置历史加载标志
          this.state.isWaitingForAgent = false;
          this.state.messages = []; // 清空AI对话历史
          if (this.state.chatWs) {
            this.state.chatWs.close();
            this.state.chatWs = null;
          }
          // 显示转人工按钮
          const transferBtn2 = this.shadowRoot.getElementById('ticket-widget-transfer');
          if (transferBtn2) {
            transferBtn2.style.display = 'block';
            transferBtn2.disabled = false;
            transferBtn2.textContent = '转人工';
          }
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
    }
  };

  // 暴露到全局
  global.TicketWidget = TicketWidget;

})(window);