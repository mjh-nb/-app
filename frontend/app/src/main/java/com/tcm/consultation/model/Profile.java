package com.tcm.consultation.model;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Profile - 问诊人档案数据模型
 * 职责：存储单个问诊人的所有信息，包括基本信息、聊天历史、上下文等
 */
public class Profile {

    // 唯一标识符（格式：profile_xxx_uuid）
    @SerializedName("user_id")
    private String userId;

    // 姓名/昵称
    @SerializedName("name")
    private String name;

    // 性别
    @SerializedName("sex")
    private String sex;

    // 年龄
    @SerializedName("age")
    private int age;

    // 聊天历史
    @SerializedName("history")
    private List<ChatMessage> history;

    // 长期记忆上下文
    @SerializedName("saved_context")
    private Map<String, Object> savedContext;

    // 创建时间
    @SerializedName("created_at")
    private long createdAt;

    // 最后更新时间
    @SerializedName("updated_at")
    private long updatedAt;

    public Profile() {
        this.history = new ArrayList<>();
        this.savedContext = new HashMap<>();
        this.createdAt = System.currentTimeMillis();
        this.updatedAt = System.currentTimeMillis();
    }

    public Profile(String userId, String name, String sex, int age) {
        this();
        this.userId = userId;
        this.name = name;
        this.sex = sex;
        this.age = age;

        // 初始化 saved_context 中的 profile 信息
        Map<String, Object> profileInfo = new HashMap<>();
        profileInfo.put("name", name);
        profileInfo.put("sex", sex);
        profileInfo.put("age", age);
        this.savedContext.put("profile", profileInfo);
    }

    // Getter 和 Setter
    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
        updateProfileInContext();
    }

    public String getSex() {
        return sex;
    }

    public void setSex(String sex) {
        this.sex = sex;
        updateProfileInContext();
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
        updateProfileInContext();
    }

    public List<ChatMessage> getHistory() {
        return history;
    }

    public void setHistory(List<ChatMessage> history) {
        this.history = history;
    }

    public Map<String, Object> getSavedContext() {
        return savedContext;
    }

    public void setSavedContext(Map<String, Object> savedContext) {
        this.savedContext = savedContext;
    }

    public long getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(long createdAt) {
        this.createdAt = createdAt;
    }

    public long getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(long updatedAt) {
        this.updatedAt = updatedAt;
    }

    /**
     * 更新 savedContext 中的 profile 信息
     */
    private void updateProfileInContext() {
        Map<String, Object> profileInfo = new HashMap<>();
        profileInfo.put("name", name);
        profileInfo.put("sex", sex);
        profileInfo.put("age", age);
        savedContext.put("profile", profileInfo);
        updatedAt = System.currentTimeMillis();
    }

    /**
     * 添加用户消息到历史
     */
    public void addUserMessage(String content) {
        ChatMessage message = ChatMessage.createUserMessage(content);
        history.add(message);
        updatedAt = System.currentTimeMillis();
    }

    /**
     * 添加助手消息到历史
     */
    public void addAssistantMessage(String content) {
        ChatMessage message = ChatMessage.createAssistantMessage(content);
        history.add(message);
        updatedAt = System.currentTimeMillis();
    }

    /**
     * 获取当前历史轮数
     */
    public int getHistoryRounds() {
        return history.size();
    }

    /**
     * 清空历史记录
     */
    public void clearHistory() {
        history.clear();
        updatedAt = System.currentTimeMillis();
    }

    /**
     * 清空 saved_context（保留 profile 基本信息）
     */
    public void clearSavedContext() {
        savedContext.clear();
        updateProfileInContext();
    }

    /**
     * 合并新的上下文到 saved_context
     */
    @SuppressWarnings("unchecked")
    public void mergeSavedContext(Map<String, Object> newContext) {
        if (newContext != null && !newContext.isEmpty()) {
            for (Map.Entry<String, Object> entry : newContext.entrySet()) {
                // profile 字段特殊处理，不覆盖本地 profile
                if ("profile".equals(entry.getKey())) {
                    continue;
                }
                savedContext.put(entry.getKey(), entry.getValue());
            }
            updatedAt = System.currentTimeMillis();
        }
    }

    /**
     * 获取显示名称（如果名字为空则显示默认值）
     */
    public String getDisplayName() {
        if (name == null || name.trim().isEmpty()) {
            return "未命名";
        }
        return name;
    }

    /**
     * 获取性别和年龄描述
     */
    public String getGenderAgeDesc() {
        return sex + " · " + age + "岁";
    }
}
