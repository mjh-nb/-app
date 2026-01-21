package com.tcm.consultation.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.tcm.consultation.R;
import com.tcm.consultation.model.ChatMessage;

import java.util.ArrayList;
import java.util.List;

/**
 * ChatAdapter - 聊天消息列表适配器
 * 职责：管理聊天消息的显示，区分用户消息和助手消息
 */
public class ChatAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    private static final int TYPE_USER = 1;
    private static final int TYPE_ASSISTANT = 2;

    private final List<ChatMessage> messages;

    public ChatAdapter() {
        this.messages = new ArrayList<>();
    }

    @Override
    public int getItemViewType(int position) {
        ChatMessage message = messages.get(position);
        return message.isUserMessage() ? TYPE_USER : TYPE_ASSISTANT;
    }

    @NonNull
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        if (viewType == TYPE_USER) {
            View view = inflater.inflate(R.layout.item_message_user, parent, false);
            return new UserMessageViewHolder(view);
        } else {
            View view = inflater.inflate(R.layout.item_message_assistant, parent, false);
            return new AssistantMessageViewHolder(view);
        }
    }

    @Override
    public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
        ChatMessage message = messages.get(position);
        if (holder instanceof UserMessageViewHolder) {
            ((UserMessageViewHolder) holder).bind(message);
        } else if (holder instanceof AssistantMessageViewHolder) {
            ((AssistantMessageViewHolder) holder).bind(message);
        }
    }

    @Override
    public int getItemCount() {
        return messages.size();
    }

    /**
     * 设置消息列表
     */
    public void setMessages(List<ChatMessage> newMessages) {
        messages.clear();
        if (newMessages != null) {
            messages.addAll(newMessages);
        }
        notifyDataSetChanged();
    }

    /**
     * 添加消息
     */
    public void addMessage(ChatMessage message) {
        messages.add(message);
        notifyItemInserted(messages.size() - 1);
    }

    /**
     * 更新最后一条消息
     */
    public void updateLastMessage(ChatMessage message) {
        if (!messages.isEmpty()) {
            int lastIndex = messages.size() - 1;
            messages.set(lastIndex, message);
            notifyItemChanged(lastIndex);
        }
    }

    /**
     * 移除最后一条消息
     */
    public void removeLastMessage() {
        if (!messages.isEmpty()) {
            int lastIndex = messages.size() - 1;
            messages.remove(lastIndex);
            notifyItemRemoved(lastIndex);
        }
    }

    /**
     * 获取消息数量
     */
    public int getMessageCount() {
        return messages.size();
    }

    /**
     * 用户消息 ViewHolder
     */
    static class UserMessageViewHolder extends RecyclerView.ViewHolder {
        private final TextView tvContent;

        UserMessageViewHolder(@NonNull View itemView) {
            super(itemView);
            tvContent = itemView.findViewById(R.id.tv_message_content);
        }

        void bind(ChatMessage message) {
            tvContent.setText(message.getContent());
        }
    }

    /**
     * 助手消息 ViewHolder
     */
    static class AssistantMessageViewHolder extends RecyclerView.ViewHolder {
        private final TextView tvContent;
        private final ProgressBar progressBar;

        AssistantMessageViewHolder(@NonNull View itemView) {
            super(itemView);
            tvContent = itemView.findViewById(R.id.tv_message_content);
            progressBar = itemView.findViewById(R.id.progress_loading);
        }

        void bind(ChatMessage message) {
            tvContent.setText(message.getContent());

            if (message.isLoading()) {
                progressBar.setVisibility(View.VISIBLE);
            } else {
                progressBar.setVisibility(View.GONE);
            }
        }
    }
}
