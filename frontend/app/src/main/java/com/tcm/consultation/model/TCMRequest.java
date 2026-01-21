package com.tcm.consultation.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;
import java.util.Map;

/**
 * TCMRequest - 请求数据模型
 * 职责：构建发送给后端的 JSON 请求体
 * 
 * 修改 JSON 字段：修改 @SerializedName 注解的值
 */
public class TCMRequest {

    @SerializedName("user_id")
    private String userId;

    @SerializedName("request_type")
    private String requestType;

    @SerializedName("payload")
    private Payload payload;

    public TCMRequest() {
        this.requestType = "multi";
        this.payload = new Payload();
    }

    // Getter 和 Setter
    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getRequestType() {
        return requestType;
    }

    public void setRequestType(String requestType) {
        this.requestType = requestType;
    }

    public Payload getPayload() {
        return payload;
    }

    public void setPayload(Payload payload) {
        this.payload = payload;
    }

    /**
     * Payload - 请求载荷内部类
     */
    public static class Payload {

        @SerializedName("images")
        private Images images;

        @SerializedName("user_text")
        private String userText;

        @SerializedName("saved_context")
        private Map<String, Object> savedContext;

        @SerializedName("history")
        private List<ChatMessage> history;

        public Payload() {
            this.images = new Images();
        }

        // Getter 和 Setter
        public Images getImages() {
            return images;
        }

        public void setImages(Images images) {
            this.images = images;
        }

        public String getUserText() {
            return userText;
        }

        public void setUserText(String userText) {
            this.userText = userText;
        }

        public Map<String, Object> getSavedContext() {
            return savedContext;
        }

        public void setSavedContext(Map<String, Object> savedContext) {
            this.savedContext = savedContext;
        }

        public List<ChatMessage> getHistory() {
            return history;
        }

        public void setHistory(List<ChatMessage> history) {
            this.history = history;
        }
    }

    /**
     * Images - 图片数据内部类
     */
    public static class Images {

        @SerializedName("face")
        private String face;

        @SerializedName("tongue")
        private String tongue;

        // Getter 和 Setter
        public String getFace() {
            return face;
        }

        public void setFace(String face) {
            this.face = face;
        }

        public String getTongue() {
            return tongue;
        }

        public void setTongue(String tongue) {
            this.tongue = tongue;
        }

        /**
         * 判断是否有图片数据
         */
        public boolean hasImage() {
            return (face != null && !face.isEmpty()) 
                || (tongue != null && !tongue.isEmpty());
        }
    }

    /**
     * 构建器类
     */
    public static class Builder {
        private final TCMRequest request;

        public Builder() {
            request = new TCMRequest();
        }

        public Builder userId(String userId) {
            request.setUserId(userId);
            return this;
        }

        public Builder userText(String userText) {
            request.getPayload().setUserText(userText);
            return this;
        }

        public Builder faceImage(String base64) {
            request.getPayload().getImages().setFace(base64);
            return this;
        }

        public Builder tongueImage(String base64) {
            request.getPayload().getImages().setTongue(base64);
            return this;
        }

        public Builder savedContext(Map<String, Object> context) {
            request.getPayload().setSavedContext(context);
            return this;
        }

        public Builder history(List<ChatMessage> history) {
            request.getPayload().setHistory(history);
            return this;
        }

        public TCMRequest build() {
            return request;
        }
    }
}
