package com.tcm.consultation.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.tcm.consultation.R;
import com.tcm.consultation.model.Profile;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * ProfileAdapter - 问诊人列表适配器
 * 职责：显示问诊人档案列表，支持点击和删除操作
 */
public class ProfileAdapter extends RecyclerView.Adapter<ProfileAdapter.ProfileViewHolder> {

    private final List<Profile> profiles;
    private OnProfileClickListener listener;

    public ProfileAdapter() {
        this.profiles = new ArrayList<>();
    }

    @NonNull
    @Override
    public ProfileViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_profile, parent, false);
        return new ProfileViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ProfileViewHolder holder, int position) {
        Profile profile = profiles.get(position);
        holder.bind(profile, listener);
    }

    @Override
    public int getItemCount() {
        return profiles.size();
    }

    /**
     * 设置问诊人列表
     */
    public void setProfiles(List<Profile> newProfiles) {
        profiles.clear();
        if (newProfiles != null) {
            profiles.addAll(newProfiles);
        }
        notifyDataSetChanged();
    }

    /**
     * 设置点击监听器
     */
    public void setOnProfileClickListener(OnProfileClickListener listener) {
        this.listener = listener;
    }

    /**
     * ViewHolder
     */
    static class ProfileViewHolder extends RecyclerView.ViewHolder {
        private final TextView tvName;
        private final TextView tvInfo;
        private final TextView tvTime;
        private final TextView tvHistoryCount;
        private final ImageButton btnDelete;

        ProfileViewHolder(@NonNull View itemView) {
            super(itemView);
            tvName = itemView.findViewById(R.id.tv_profile_name);
            tvInfo = itemView.findViewById(R.id.tv_profile_info);
            tvTime = itemView.findViewById(R.id.tv_profile_time);
            tvHistoryCount = itemView.findViewById(R.id.tv_history_count);
            btnDelete = itemView.findViewById(R.id.btn_delete);
        }

        void bind(Profile profile, OnProfileClickListener listener) {
            tvName.setText(profile.getDisplayName());
            tvInfo.setText(profile.getGenderAgeDesc());

            // 格式化时间
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA);
            tvTime.setText("最后更新：" + sdf.format(new Date(profile.getUpdatedAt())));

            // 显示历史记录数
            int historyCount = profile.getHistoryRounds();
            tvHistoryCount.setText(historyCount + " 条记录");

            // 点击事件
            itemView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onProfileClick(profile);
                }
            });

            btnDelete.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onProfileDelete(profile);
                }
            });
        }
    }

    /**
     * 点击监听接口
     */
    public interface OnProfileClickListener {
        void onProfileClick(Profile profile);
        void onProfileDelete(Profile profile);
    }
}
