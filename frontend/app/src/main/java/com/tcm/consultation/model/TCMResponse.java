package com.tcm.consultation.model;

import com.google.gson.annotations.SerializedName;

import java.util.Map;

/**
 * TCMResponse - 响应数据模型
 * 职责：解析后端返回的 JSON 响应
 * 
 * 修改 JSON 字段：修改 @SerializedName 注解的值
 */
public class TCMResponse {

    @SerializedName("status")
    private String status;

    @SerializedName("message")
    private String message;

    @SerializedName("data")
    private Data data;

    // Getter 和 Setter
    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Data getData() {
        return data;
    }

    public void setData(Data data) {
        this.data = data;
    }

    /**
     * 判断请求是否成功
     */
    public boolean isSuccess() {
        return "success".equals(status);
    }

    /**
     * 获取回复文本（便捷方法）
     */
    public String getReplyText() {
        if (data != null) {
            return data.getReplyText();
        }
        return null;
    }

    /**
     * 获取新上下文（便捷方法）
     */
    public Map<String, Object> getNewContext() {
        if (data != null && data.isHasNewContext()) {
            return data.getNewContextToSave();
        }
        return null;
    }

    /**
     * Data - 响应数据内部类
     */
    public static class Data {

        @SerializedName("reply_text")
        private String replyText;

        @SerializedName("has_new_context")
        private boolean hasNewContext;

        @SerializedName("new_context_to_save")
        private Map<String, Object> newContextToSave;

        // Getter 和 Setter
        public String getReplyText() {
            return replyText;
        }

        public void setReplyText(String replyText) {
            this.replyText = replyText;
        }

        public boolean isHasNewContext() {
            return hasNewContext;
        }

        public void setHasNewContext(boolean hasNewContext) {
            this.hasNewContext = hasNewContext;
        }

        public Map<String, Object> getNewContextToSave() {
            return newContextToSave;
        }

        public void setNewContextToSave(Map<String, Object> newContextToSave) {
            this.newContextToSave = newContextToSave;
        }
    }
}
