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
      lastPongTime: null
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
          this.verifyToken(token).then(isValid => {
            if (isValid) {
              console.log('Token is valid, re-rendering widget');
              // 重新创建 widget 以显示登录后的界面
              this.createWidget();
              this.attachEventListeners();
              this.createWidget();
              this.attachEventListeners();
              // 连接 WebSocket，会自动加入之前的会话
              this.connectWebSocket();
              // 同时连接聊天 WebSocket
              setTimeout(() => {
                if (this.state.token) {
                  this.connectChatWebSocket();
                }
              }, 500);
            } else {
              console.log('Token is invalid, clearing login state');
              this.clearLoginState();
            }
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

      localStorage.removeItem('widget_token');
      localStorage.removeItem('widget_user_id');
      localStorage.removeItem('widget_username');
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
        }

        .ticket-widget-sender {
          font-size: 12px;
          color: #999;
          margin-bottom: 4px;
          padding-left: 4px;
        }

        .ticket-widget-message.user .ticket-widget-sender {
          display: none;
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
      window.classList.toggle('open');
      this.state.isOpen = window.classList.contains('open');
    },

    closeWindow() {
      const window = this.shadowRoot.getElementById('ticket-widget-window');
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
        this.connectWebSocket();

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
          // 显示智能体回复
          this.addMessage(data.response, 'agent');

          // 如果创建了工单（根据意图判断），显示工单信息
          if (data.ticket_info && data.ticket_info.ticket_no && data.intent === 'create_ticket') {
            const ticketInfo = document.createElement('div');
            ticketInfo.className = 'ticket-widget-message agent';
            ticketInfo.innerHTML = `
              <div class="ticket-widget-message-content" style="background: #f6ffed; border: 1px solid #b7eb8f;">
                <div style="font-weight: bold; margin-bottom: 4px;">📝 工单已创建</div>
                <div>编号：${data.ticket_info.ticket_no}</div>
                <div>标题：${data.ticket_info.title}</div>
                <div>优先级：${data.ticket_info.priority || 'normal'}</div>
              </div>
            `;
            const body = this.shadowRoot.getElementById('ticket-widget-body');
            body.appendChild(ticketInfo);
            body.scrollTop = body.scrollHeight;
          }
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
      const messageDiv = document.createElement('div');
      messageDiv.className = `ticket-widget-message ${type}`;

      // 转义HTML并将换行符转为<br>
      const formattedContent = this.escapeHtml(content).replace(/\n/g, '<br>');

      // 如果有发送者名称且不是用户自己，显示发送者
      let senderHtml = '';
      if (senderName && type !== 'user') {
        senderHtml = `<div class="ticket-widget-sender">${this.escapeHtml(senderName)}</div>`;
      }

      messageDiv.innerHTML = `
        ${senderHtml}
        <div class="ticket-widget-message-content">${formattedContent}</div>
      `;
      body.appendChild(messageDiv);
      body.scrollTop = body.scrollHeight;
    },

    // 加载聊天历史消息
    async loadChatHistory(sessionId) {
      try {
        console.log('Loading chat history for session:', sessionId);
        const response = await this.apiRequest(
          `${this.config.apiUrl}/chat-service/sessions/${sessionId}/messages?page=1&page_size=50`
        );

        if (!response.ok) {
          console.error('Failed to load chat history:', response.status);
          return;
        }

        const data = await response.json();
        console.log('Loaded chat history:', data);

        if (data.items && data.items.length > 0) {
          // 清空当前消息区域（保留系统提示）
          const body = this.shadowRoot.getElementById('ticket-widget-body');
          // 找到系统提示后的位置，或者清空所有消息
          body.innerHTML = '';

          // 添加历史消息
          data.items.forEach(msg => {
            let msgType;
            let senderName = null;

            if (msg.sender_type === 'agent') {
              msgType = 'human';
              senderName = msg.sender?.name || '客服';
            } else if (msg.sender_type === 'customer') {
              msgType = 'user';
            } else {
              msgType = 'system';
              senderName = msg.sender?.name || '系统';
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = `ticket-widget-message ${msgType}`;

            const formattedContent = this.escapeHtml(msg.content).replace(/\n/g, '<br>');
            let senderHtml = '';
            if (senderName && msgType !== 'user') {
              senderHtml = `<div class="ticket-widget-sender">${this.escapeHtml(senderName)}</div>`;
            }

            messageDiv.innerHTML = `
              ${senderHtml}
              <div class="ticket-widget-message-content">${formattedContent}</div>
            `;
            body.appendChild(messageDiv);
          });

          // 滚动到底部
          body.scrollTop = body.scrollHeight;
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
      }
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
          const data = JSON.parse(event.data);
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

        this.state.ws.onclose = () => {
          console.log('WebSocket closed');
          // 清理心跳
          this._stopHeartbeat();
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
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
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
        const response = await this.apiRequest(`${this.config.apiUrl}/chat-service/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            request_type: 'general',
            message: '客户请求转人工'
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
          const agentName = data.agent?.name || '客服';
          this.addMessage(`客服 ${agentName} 已为您服务`, 'system');

          // 隐藏转人工按钮
          if (transferBtn) {
            transferBtn.style.display = 'none';
          }

          // 连接聊天WebSocket
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
        // 否则等待服务器的 session_rejoined 消息
        if (sessionId) {
          ws.send(JSON.stringify({
            type: 'join_session',
            session_id: sessionId,
            role: 'customer'
          }));
          // 加载历史消息
          this.loadChatHistory(sessionId);
        } else {
          console.log('No sessionId provided, waiting for session_rejoined from server');
        }
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
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

      ws.onclose = () => {
        console.log('Chat WebSocket closed');
        // 清理心跳
        if (this.state.chatWsHeartbeatInterval) {
          clearInterval(this.state.chatWsHeartbeatInterval);
          this.state.chatWsHeartbeatInterval = null;
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
          this.addMessage(`客服 ${agentName} 已接入会话`, 'system');

          // 隐藏转人工按钮
          const transferBtn = this.shadowRoot.getElementById('ticket-widget-transfer');
          if (transferBtn) {
            transferBtn.style.display = 'none';
          }

          // 加载历史消息
          this.loadChatHistory(data.session_id);
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
            this.addMessage(data.message || '会话已结束，已回到AI模式', 'system');
            this.loadChatHistory(data.session_id);
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
          this.addMessage(data.message || '已重新连接到会话', 'system');

          // 隐藏转人工按钮
          const transferBtnRejoin = this.shadowRoot.getElementById('ticket-widget-transfer');
          if (transferBtnRejoin) {
            transferBtnRejoin.style.display = 'none';
          }

          // 加载历史消息
          this.loadChatHistory(data.session_id);

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

          // 添加历史记录提示
          this.addMessage('━━━━━━━━━━━━━━━━━━━━', 'system');
          this.addMessage(data.message || '会话已结束，以下是历史记录', 'system');
          this.addMessage('━━━━━━━━━━━━━━━━━━━━', 'system');

          this.loadChatHistory(data.session_id);

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
          this.state.isWaitingForAgent = false;
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