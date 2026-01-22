package com.tcm.consultation.model;

import com.google.gson.annotations.SerializedName;

/**
 * ChatMessage - 聊天消息数据模型
 * 职责：表示单条聊天消息，用于 UI 展示和 history 构建
 * 
 * 修改 JSON 字段：修改 @SerializedName 注解的值
 */
public class ChatMessage {

    // 消息角色：user 或 assistant
    @SerializedName("role")
    private String role;

    // 消息内容
    @SerializedName("content")
    private String content;

    // 消息 ID（仅本地使用，不传给后端）
    private transient String messageId;

    // 是否为加载中状态（仅本地使用）
    private transient boolean isLoading;

    // 时间戳（仅本地使用）
    private transient long timestamp;

    public ChatMessage() {
    }

    public ChatMessage(String role, String content) {
        this.role = role;
        this.content = content;
        this.timestamp = System.currentTimeMillis();
    }

    // Getter 和 Setter
    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getMessageId() {
        return messageId;
    }

    public void setMessageId(String messageId) {
        this.messageId = messageId;
    }

    public boolean isLoading() {
        return isLoading;
    }

    public void setLoading(boolean loading) {
        isLoading = loading;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    /**
     * 判断是否为用户消息
     */
    public boolean isUserMessage() {
        return "user".equals(role);
    }

    /**
     * 判断是否为助手消息
     */
    public boolean isAssistantMessage() {
        return "assistant".equals(role);
    }

    /**
     * 创建用户消息
     */
    public static ChatMessage createUserMessage(String content) {
        ChatMessage message = new ChatMessage("user", content);
        return message;
    }

    /**
     * 创建助手消息
     */
    public static ChatMessage createAssistantMessage(String content) {
        ChatMessage message = new ChatMessage("assistant", content);
        return message;
    }

    /**
     * 创建加载中消息
     */
    public static ChatMessage createLoadingMessage() {
        ChatMessage message = new ChatMessage("assistant", "正在分析，请稍候…");
        message.setLoading(true);
        return message;
    }
}
