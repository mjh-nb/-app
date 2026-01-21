package com.tcm.consultation.utils;

/**
 * Constants - 全局常量配置类
 * 职责：集中管理所有可配置的常量值
 * 
 * 修改说明：
 * - 修改服务器地址：修改 BASE_URL 和 API_ENDPOINT
 * - 修改轮数上限：修改 MAX_HISTORY_ROUNDS
 * - 修改请求超时：修改 REQUEST_TIMEOUT_SECONDS
 */
public final class Constants {

    private Constants() {
        // 防止实例化
    }

    // ==================== 服务器配置 ====================
    // 后端服务器基础地址（修改服务器地址改这里）
    public static final String BASE_URL = "https://7244bb50.r38.cpolar.top";

    // API 端点路径
    public static final String API_ENDPOINT = "/api/tcm_process";

    // 完整 API 地址
    public static final String API_URL = BASE_URL + API_ENDPOINT;

    // ==================== 对话配置 ====================
    // 最大历史轮数（修改轮数上限改这里）
    public static final int MAX_HISTORY_ROUNDS = 50;

    // 请求类型（固定值）
    public static final String REQUEST_TYPE = "multi";

    // ==================== 网络配置 ====================
    // 连接超时（秒）
    public static final int CONNECT_TIMEOUT_SECONDS = 30;

    // 读取超时（秒）
    public static final int READ_TIMEOUT_SECONDS = 120;

    // 写入超时（秒）
    public static final int WRITE_TIMEOUT_SECONDS = 60;

    // ==================== 图片配置 ====================
    // 图片压缩最大宽度（像素）
    public static final int IMAGE_MAX_WIDTH = 800;

    // 图片压缩最大高度（像素）
    public static final int IMAGE_MAX_HEIGHT = 800;

    // JPEG 压缩质量（0-100）
    public static final int IMAGE_QUALITY = 80;

    // ==================== 存储键名 ====================
    // SharedPreferences 文件名
    public static final String PREFS_NAME = "tcm_consultation_prefs";

    // 问诊人列表键名
    public static final String KEY_PROFILES = "profiles";

    // 当前选中问诊人 ID 键名
    public static final String KEY_CURRENT_PROFILE_ID = "current_profile_id";

    // ==================== 角色标识 ====================
    // 用户角色
    public static final String ROLE_USER = "user";

    // 助手角色
    public static final String ROLE_ASSISTANT = "assistant";

    // ==================== 响应状态 ====================
    // 成功状态
    public static final String STATUS_SUCCESS = "success";

    // ==================== 性别选项 ====================
    public static final String GENDER_MALE = "男";
    public static final String GENDER_FEMALE = "女";
    public static final String GENDER_OTHER = "其他";

    // ==================== 图片类型 ====================
    public static final int IMAGE_TYPE_FACE = 1;
    public static final int IMAGE_TYPE_TONGUE = 2;
}
