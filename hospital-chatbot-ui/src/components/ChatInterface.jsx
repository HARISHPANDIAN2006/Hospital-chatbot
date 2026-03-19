import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Bot, Hospital, Search, UserPlus, Calendar } from 'lucide-react';

const API_BASE_URL = 'http://localhost:3333';

function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      content: '👋 Hello! I\'m your hospital assistant. I can help you with:\n• Registering new patients\n• Searching for doctors\n• Booking appointments\n\nHow can I help you today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText = input) => {
    if (!messageText.trim()) return;

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        query: messageText
      });

      const botMessage = {
        role: 'bot',
        content: response.data.human_response || JSON.stringify(response.data, null, 2),
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'bot',
        content: `Sorry, I encountered an error: ${error.message}\n\nPlease make sure the backend server is running on port 3333.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { icon: Search, text: 'Find cardiologists', color: 'blue' },
    { icon: UserPlus, text: 'Register new patient', color: 'green' },
    { icon: Calendar, text: 'Book appointment', color: 'purple' }
  ];

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 shadow-lg">
        <div className="flex items-center gap-3">
          <Hospital size={32} />
          <div>
            <h1 className="text-2xl font-bold">Hospital Management Chatbot</h1>
            <p className="text-blue-100 text-sm">AI-powered healthcare assistant</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow-sm p-4 flex gap-3 overflow-x-auto">
        {quickActions.map((action, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(action.text)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 border-${action.color}-500 text-${action.color}-600 hover:bg-${action.color}-500 hover:text-white transition-all whitespace-nowrap`}
          >
            <action.icon size={18} />
            <span className="text-sm font-medium">{action.text}</span>
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex gap-3 max-w-[70%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {/* Avatar */}
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-blue-500 to-blue-600' 
                  : 'bg-gradient-to-br from-purple-500 to-purple-600'
              }`}>
                {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
              </div>

              {/* Message Bubble */}
              <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                    : 'bg-white text-gray-800 shadow-md border border-gray-100'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                <span className="text-xs text-gray-500 mt-1">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="flex gap-3 max-w-[70%]">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                <Bot size={20} className="text-white" />
              </div>
              <div className="bg-white rounded-2xl px-4 py-3 shadow-md">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-full focus:border-blue-500 focus:outline-none transition-colors"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-full hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
          >
            <Send size={20} />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;