package com.tcm.consultation.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.tcm.consultation.R;
import com.tcm.consultation.model.Profile;
import com.tcm.consultation.storage.ProfileStorage;

import java.util.List;

/**
 * ProfileActivity - 问诊人档案管理页
 * 职责：显示问诊人列表，支持选择、新建、删除问诊人档案
 */
public class ProfileActivity extends AppCompatActivity implements ProfileAdapter.OnProfileClickListener {

    private RecyclerView recyclerView;
    private ProfileAdapter adapter;
    private LinearLayout layoutEmpty;  // 修复：改为 LinearLayout
    private ProfileStorage storage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_profile);

        storage = ProfileStorage.getInstance(this);

        initToolbar();
        initViews();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadProfiles();
    }

    private void initToolbar() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle("选择问诊人");
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        toolbar.setNavigationOnClickListener(v -> onBackPressed());
    }

    private void initViews() {
        recyclerView = findViewById(R.id.recycler_profiles);
        layoutEmpty = findViewById(R.id.tv_empty);  // 修复：改为 LinearLayout

        // 设置 RecyclerView
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ProfileAdapter();
        adapter.setOnProfileClickListener(this);
        recyclerView.setAdapter(adapter);

        // 新建问诊人按钮
        FloatingActionButton fabAdd = findViewById(R.id.fab_add);
        fabAdd.setOnClickListener(v -> {
            Intent intent = new Intent(this, ProfileEditActivity.class);
            startActivity(intent);
        });
    }

    private void loadProfiles() {
        List<Profile> profiles = storage.getAllProfiles();
        adapter.setProfiles(profiles);

        if (profiles.isEmpty()) {
            layoutEmpty.setVisibility(View.VISIBLE);  // 修复：使用 layoutEmpty
            recyclerView.setVisibility(View.GONE);
        } else {
            layoutEmpty.setVisibility(View.GONE);  // 修复：使用 layoutEmpty
            recyclerView.setVisibility(View.VISIBLE);
        }
    }

    @Override
    public void onProfileClick(Profile profile) {
        // 设置当前选中的问诊人
        storage.setCurrentProfileId(profile.getUserId());

        // 跳转到聊天页
        Intent intent = new Intent(this, ChatActivity.class);
        startActivity(intent);
    }

    @Override
    public void onProfileDelete(Profile profile) {
        // 弹出确认对话框
        new AlertDialog.Builder(this)
                .setTitle("删除问诊人")
                .setMessage("确定要删除「" + profile.getDisplayName() + "」的所有问诊记录吗？此操作不可恢复。")
                .setPositiveButton("删除", (dialog, which) -> {
                    storage.deleteProfile(profile.getUserId());
                    loadProfiles();
                })
                .setNegativeButton("取消", null)
                .show();
    }
}
