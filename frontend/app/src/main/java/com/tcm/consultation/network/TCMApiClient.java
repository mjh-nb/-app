package com.tcm.consultation.network;

import android.os.Handler;
import android.os.Looper;

import androidx.annotation.NonNull;

import com.google.gson.Gson;
import com.tcm.consultation.model.TCMRequest;
import com.tcm.consultation.model.TCMResponse;
import com.tcm.consultation.utils.Constants;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.ResponseBody;

/**
 * TCMApiClient - 网络请求客户端
 * 职责：封装 OkHttp，处理与后端的 HTTP 通信
 * 
 * 修改服务器地址：修改 Constants.java 中的 API_URL
 */
public class TCMApiClient {

    private static TCMApiClient instance;
    private final OkHttpClient client;
    private final Gson gson;
    private final Handler mainHandler;

    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");

    private TCMApiClient() {
        // 配置 OkHttpClient
        client = new OkHttpClient.Builder()
                .connectTimeout(Constants.CONNECT_TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .readTimeout(Constants.READ_TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .writeTimeout(Constants.WRITE_TIMEOUT_SECONDS, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true)
                .build();

        gson = new Gson();
        mainHandler = new Handler(Looper.getMainLooper());
    }

    /**
     * 获取单例实例
     */
    public static synchronized TCMApiClient getInstance() {
        if (instance == null) {
            instance = new TCMApiClient();
        }
        return instance;
    }

    /**
     * 发送问诊请求
     * 
     * @param tcmRequest 请求数据
     * @param callback   回调接口
     */
    public void sendConsultation(TCMRequest tcmRequest, final ApiCallback callback) {
        // 将请求对象转换为 JSON
        String jsonBody = gson.toJson(tcmRequest);

        // 构建请求体
        RequestBody body = RequestBody.create(jsonBody, JSON);

        // 构建请求
        Request request = new Request.Builder()
                .url(Constants.API_URL)
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build();

        // 异步执行请求
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                // 网络请求失败，切回主线程回调
                mainHandler.post(() -> {
                    if (callback != null) {
                        callback.onError(parseErrorMessage(e));
                    }
                });
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) {
                try {
                    ResponseBody responseBody = response.body();
                    if (responseBody == null) {
                        mainHandler.post(() -> {
                            if (callback != null) {
                                callback.onError("服务器返回空响应");
                            }
                        });
                        return;
                    }

                    String responseJson = responseBody.string();

                    if (!response.isSuccessful()) {
                        mainHandler.post(() -> {
                            if (callback != null) {
                                callback.onError("服务器错误：" + response.code());
                            }
                        });
                        return;
                    }

                    // 解析响应 JSON
                    TCMResponse tcmResponse = gson.fromJson(responseJson, TCMResponse.class);

                    // 切回主线程回调
                    mainHandler.post(() -> {
                        if (callback != null) {
                            if (tcmResponse != null && tcmResponse.isSuccess()) {
                                callback.onSuccess(tcmResponse);
                            } else {
                                String errorMsg = "请求失败";
                                if (tcmResponse != null && tcmResponse.getMessage() != null) {
                                    errorMsg = tcmResponse.getMessage();
                                }
                                callback.onError(errorMsg);
                            }
                        }
                    });

                } catch (Exception e) {
                    mainHandler.post(() -> {
                        if (callback != null) {
                            callback.onError("数据解析失败：" + e.getMessage());
                        }
                    });
                }
            }
        });
    }

    /**
     * 解析错误信息
     */
    private String parseErrorMessage(IOException e) {
        String message = e.getMessage();
        if (message == null) {
            return "网络请求失败";
        }

        if (message.contains("timeout")) {
            return "请求超时，请检查网络后重试";
        } else if (message.contains("Unable to resolve host")) {
            return "无法连接服务器，请检查网络设置";
        } else if (message.contains("Connection refused")) {
            return "服务器拒绝连接，请稍后重试";
        } else if (message.contains("Failed to connect")) {
            return "连接服务器失败，请检查网络";
        }

        return "网络错误：" + message;
    }

    /**
     * 取消所有请求
     */
    public void cancelAll() {
        client.dispatcher().cancelAll();
    }

    /**
     * API 回调接口
     */
    public interface ApiCallback {
        /**
         * 请求成功
         */
        void onSuccess(TCMResponse response);

        /**
         * 请求失败
         */
        void onError(String errorMessage);
    }
}
