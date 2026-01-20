package com.tcm.consultation.storage;

import android.content.Context;
import android.content.SharedPreferences;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.tcm.consultation.model.Profile;
import com.tcm.consultation.utils.Constants;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

/**
 * ProfileStorage - 问诊人档案存储管理类
 * 职责：管理问诊人档案的本地持久化存储（SharedPreferences）
 */
public class ProfileStorage {

    private static ProfileStorage instance;
    private final SharedPreferences prefs;
    private final Gson gson;

    // 内存缓存
    private List<Profile> profileCache;
    private String currentProfileIdCache;

    private ProfileStorage(Context context) {
        prefs = context.getApplicationContext()
                .getSharedPreferences(Constants.PREFS_NAME, Context.MODE_PRIVATE);
        gson = new Gson();
    }

    /**
     * 获取单例实例
     */
    public static synchronized ProfileStorage getInstance(Context context) {
        if (instance == null) {
            instance = new ProfileStorage(context);
        }
        return instance;
    }

    /**
     * 获取所有问诊人档案列表
     */
    public List<Profile> getAllProfiles() {
        if (profileCache == null) {
            String json = prefs.getString(Constants.KEY_PROFILES, null);
            if (json != null && !json.isEmpty()) {
                Type type = new TypeToken<List<Profile>>() {}.getType();
                profileCache = gson.fromJson(json, type);
            }
            if (profileCache == null) {
                profileCache = new ArrayList<>();
            }
        }
        return new ArrayList<>(profileCache);
    }

    /**
     * 保存所有问诊人档案列表
     */
    private void saveAllProfiles(List<Profile> profiles) {
        profileCache = new ArrayList<>(profiles);
        String json = gson.toJson(profiles);
        prefs.edit().putString(Constants.KEY_PROFILES, json).apply();
    }

    /**
     * 根据 ID 获取问诊人档案
     */
    public Profile getProfileById(String userId) {
        List<Profile> profiles = getAllProfiles();
        for (Profile profile : profiles) {
            if (profile.getUserId().equals(userId)) {
                return profile;
            }
        }
        return null;
    }

    /**
     * 添加新的问诊人档案
     */
    public void addProfile(Profile profile) {
        List<Profile> profiles = getAllProfiles();
        profiles.add(profile);
        saveAllProfiles(profiles);
    }

    /**
     * 更新问诊人档案
     */
    public void updateProfile(Profile profile) {
        List<Profile> profiles = getAllProfiles();
        for (int i = 0; i < profiles.size(); i++) {
            if (profiles.get(i).getUserId().equals(profile.getUserId())) {
                profile.setUpdatedAt(System.currentTimeMillis());
                profiles.set(i, profile);
                saveAllProfiles(profiles);
                return;
            }
        }
    }

    /**
     * 删除问诊人档案
     */
    public void deleteProfile(String userId) {
        List<Profile> profiles = getAllProfiles();
        profiles.removeIf(p -> p.getUserId().equals(userId));
        saveAllProfiles(profiles);

        // 如果删除的是当前选中的档案，清除选中状态
        if (userId.equals(getCurrentProfileId())) {
            setCurrentProfileId(null);
        }
    }

    /**
     * 获取当前选中的问诊人 ID
     */
    public String getCurrentProfileId() {
        if (currentProfileIdCache == null) {
            currentProfileIdCache = prefs.getString(Constants.KEY_CURRENT_PROFILE_ID, null);
        }
        return currentProfileIdCache;
    }

    /**
     * 设置当前选中的问诊人 ID
     */
    public void setCurrentProfileId(String userId) {
        currentProfileIdCache = userId;
        if (userId == null) {
            prefs.edit().remove(Constants.KEY_CURRENT_PROFILE_ID).apply();
        } else {
            prefs.edit().putString(Constants.KEY_CURRENT_PROFILE_ID, userId).apply();
        }
    }

    /**
     * 获取当前选中的问诊人档案
     */
    public Profile getCurrentProfile() {
        String currentId = getCurrentProfileId();
        if (currentId != null) {
            return getProfileById(currentId);
        }
        return null;
    }

    /**
     * 判断是否存在问诊人档案
     */
    public boolean hasProfiles() {
        return !getAllProfiles().isEmpty();
    }

    /**
     * 清除所有数据（用于测试或重置）
     */
    public void clearAll() {
        profileCache = null;
        currentProfileIdCache = null;
        prefs.edit()
                .remove(Constants.KEY_PROFILES)
                .remove(Constants.KEY_CURRENT_PROFILE_ID)
                .apply();
    }

    /**
     * 刷新缓存
     */
    public void refreshCache() {
        profileCache = null;
        currentProfileIdCache = null;
    }
}
