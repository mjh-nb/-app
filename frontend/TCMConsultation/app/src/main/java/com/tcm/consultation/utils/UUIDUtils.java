package com.tcm.consultation.utils;

import java.util.UUID;

/**
 * UUIDUtils - UUID 生成工具类
 * 职责：生成唯一标识符
 */
public final class UUIDUtils {

    private UUIDUtils() {
        // 防止实例化
    }

    /**
     * 生成带前缀的 UUID
     * 格式：profile_xxx_uuid
     */
    public static String generateProfileId() {
        String uuid = UUID.randomUUID().toString().replace("-", "");
        return "profile_" + uuid.substring(0, 8) + "_" + uuid.substring(8, 16);
    }

    /**
     * 生成消息 ID
     */
    public static String generateMessageId() {
        return "msg_" + UUID.randomUUID().toString().replace("-", "").substring(0, 16);
    }
}
