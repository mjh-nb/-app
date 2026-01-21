package com.tcm.consultation;

import android.app.Application;

/**
 * TCMApplication - 应用程序入口类
 * 职责：初始化全局配置与单例组件
 */
public class TCMApplication extends Application {

    private static TCMApplication instance;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
    }

    public static TCMApplication getInstance() {
        return instance;
    }
}
