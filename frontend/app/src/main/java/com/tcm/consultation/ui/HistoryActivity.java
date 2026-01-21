package com.tcm.consultation.ui;

import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.tcm.consultation.R;
import com.tcm.consultation.model.ChatMessage;
import com.tcm.consultation.model.Profile;
import com.tcm.consultation.storage.ProfileStorage;

import java.util.List;

/**
 * HistoryActivity - 问诊历史记录查看页
 * 职责：只读方式查看某个问诊人的历史对话记录
 */
public class HistoryActivity extends AppCompatActivity {

    public static final String EXTRA_PROFILE_ID = "profile_id";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_history);

        initToolbar();
        loadHistory();
    }

    private void initToolbar() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle("历史记录");
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        toolbar.setNavigationOnClickListener(v -> onBackPressed());
    }

    private void loadHistory() {
        String profileId = getIntent().getStringExtra(EXTRA_PROFILE_ID);
        if (profileId == null) {
            finish();
            return;
        }

        ProfileStorage storage = ProfileStorage.getInstance(this);
        Profile profile = storage.getProfileById(profileId);

        if (profile == null) {
            finish();
            return;
        }

        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle(profile.getDisplayName() + " 的历史记录");
        }

        RecyclerView recyclerView = findViewById(R.id.recycler_history);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));

        ChatAdapter adapter = new ChatAdapter();
        recyclerView.setAdapter(adapter);

        List<ChatMessage> history = profile.getHistory();
        adapter.setMessages(history);
    }
}
