package com.tcm.consultation.ui;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.tcm.consultation.R;

/**
 * MainActivity - 应用主页
 * 职责：展示应用入口，提供开始问诊按钮和合规声明
 */
public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
    }

    private void initViews() {
        // 开始问诊按钮
        Button btnStart = findViewById(R.id.btn_start_consultation);
        btnStart.setOnClickListener(v -> {
            Intent intent = new Intent(this, ProfileActivity.class);
            startActivity(intent);
        });

        // 合规声明
        TextView tvDisclaimer = findViewById(R.id.tv_disclaimer);
        tvDisclaimer.setText(getString(R.string.disclaimer));
    }
}
