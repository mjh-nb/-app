package com.tcm.consultation.ui;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.bumptech.glide.Glide;
import com.tcm.consultation.R;
import com.tcm.consultation.model.ChatMessage;
import com.tcm.consultation.model.Profile;
import com.tcm.consultation.model.TCMRequest;
import com.tcm.consultation.model.TCMResponse;
import com.tcm.consultation.network.TCMApiClient;
import com.tcm.consultation.storage.ProfileStorage;
import com.tcm.consultation.utils.Constants;
import com.tcm.consultation.utils.ImageUtils;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * ChatActivity - 聊天问诊页
 * 职责：核心问诊功能，包括文本输入、图片上传、消息显示、网络请求等
 */
public class ChatActivity extends AppCompatActivity {

    private RecyclerView recyclerView;
    private ChatAdapter adapter;
    private EditText etInput;
    private ImageButton btnSend;

    private LinearLayout layoutTonguePreview;
    private LinearLayout layoutFacePreview;
    private ImageView ivTonguePreview;
    private ImageView ivFacePreview;

    private ProfileStorage storage;
    private Profile currentProfile;

    private String tongueBase64;
    private String faceBase64;
    private Uri tongueUri;
    private Uri faceUri;
    private String currentPhotoPath;
    private int currentImageType;
    private boolean isSending = false;

    private static final int PERMISSION_REQUEST_CAMERA = 100;

    private ActivityResultLauncher<Intent> tongueGalleryLauncher;
    private ActivityResultLauncher<Intent> faceGalleryLauncher;
    private ActivityResultLauncher<Uri> tongueCameraLauncher;
    private ActivityResultLauncher<Uri> faceCameraLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat);

        storage = ProfileStorage.getInstance(this);

        initLaunchers();
        initToolbar();
        initViews();
        loadCurrentProfile();
    }

    private void initLaunchers() {
        tongueGalleryLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        handleImageResult(result.getData().getData(), Constants.IMAGE_TYPE_TONGUE);
                    }
                });

        faceGalleryLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        handleImageResult(result.getData().getData(), Constants.IMAGE_TYPE_FACE);
                    }
                });

        tongueCameraLauncher = registerForActivityResult(
                new ActivityResultContracts.TakePicture(),
                success -> {
                    if (success && currentPhotoPath != null) {
                        handleCameraResult(currentPhotoPath, Constants.IMAGE_TYPE_TONGUE);
                    }
                });

        faceCameraLauncher = registerForActivityResult(
                new ActivityResultContracts.TakePicture(),
                success -> {
                    if (success && currentPhotoPath != null) {
                        handleCameraResult(currentPhotoPath, Constants.IMAGE_TYPE_FACE);
                    }
                });
    }

    private void initToolbar() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        toolbar.setNavigationOnClickListener(v -> onBackPressed());
    }

    private void initViews() {
        recyclerView = findViewById(R.id.recycler_messages);
        etInput = findViewById(R.id.et_input);
        btnSend = findViewById(R.id.btn_send);
        ImageButton btnTongue = findViewById(R.id.btn_tongue);
        ImageButton btnFace = findViewById(R.id.btn_face);

        layoutTonguePreview = findViewById(R.id.layout_tongue_preview);
        layoutFacePreview = findViewById(R.id.layout_face_preview);
        ivTonguePreview = findViewById(R.id.iv_tongue_preview);
        ivFacePreview = findViewById(R.id.iv_face_preview);
        ImageButton btnTongueRemove = findViewById(R.id.btn_tongue_remove);
        ImageButton btnFaceRemove = findViewById(R.id.btn_face_remove);

        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        layoutManager.setStackFromEnd(true);
        recyclerView.setLayoutManager(layoutManager);
        adapter = new ChatAdapter();
        recyclerView.setAdapter(adapter);

        etInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}
            @Override
            public void afterTextChanged(Editable s) {
                updateSendButtonState();
            }
        });

        btnSend.setOnClickListener(v -> sendMessage());
        btnTongue.setOnClickListener(v -> showImagePickerDialog(Constants.IMAGE_TYPE_TONGUE));
        btnFace.setOnClickListener(v -> showImagePickerDialog(Constants.IMAGE_TYPE_FACE));
        btnTongueRemove.setOnClickListener(v -> removeTongueImage());
        btnFaceRemove.setOnClickListener(v -> removeFaceImage());
        ivTonguePreview.setOnClickListener(v -> showImagePickerDialog(Constants.IMAGE_TYPE_TONGUE));
        ivFacePreview.setOnClickListener(v -> showImagePickerDialog(Constants.IMAGE_TYPE_FACE));

        updateSendButtonState();
    }

    private void loadCurrentProfile() {
        currentProfile = storage.getCurrentProfile();
        if (currentProfile == null) {
            Toast.makeText(this, "未选择问诊人", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle(currentProfile.getDisplayName() + " 的问诊");
        }

        List<ChatMessage> history = currentProfile.getHistory();
        adapter.setMessages(history);

        if (!history.isEmpty()) {
            recyclerView.scrollToPosition(history.size() - 1);
        }
    }

    private void updateSendButtonState() {
        String text = etInput.getText().toString().trim();
        boolean hasText = !TextUtils.isEmpty(text);
        boolean hasImage = tongueBase64 != null || faceBase64 != null;
        boolean canSend = (hasText || hasImage) && !isSending;

        btnSend.setEnabled(canSend);
        btnSend.setAlpha(canSend ? 1.0f : 0.5f);
    }

    private void sendMessage() {
        if (currentProfile.getHistoryRounds() >= Constants.MAX_HISTORY_ROUNDS) {
            showHistoryLimitDialog();
            return;
        }

        String userText = etInput.getText().toString().trim();

        if (TextUtils.isEmpty(userText) && tongueBase64 == null && faceBase64 == null) {
            Toast.makeText(this, "请输入文字或上传图片", Toast.LENGTH_SHORT).show();
            return;
        }

        StringBuilder contentBuilder = new StringBuilder();
        if (!TextUtils.isEmpty(userText)) {
            contentBuilder.append(userText);
        }
        if (tongueBase64 != null) {
            if (contentBuilder.length() > 0) contentBuilder.append(" ");
            contentBuilder.append("[舌像]");
        }
        if (faceBase64 != null) {
            if (contentBuilder.length() > 0) contentBuilder.append(" ");
            contentBuilder.append("[面像]");
        }

        String displayContent = contentBuilder.toString();

        ChatMessage userMessage = ChatMessage.createUserMessage(displayContent);
        adapter.addMessage(userMessage);
        currentProfile.addUserMessage(displayContent);

        ChatMessage loadingMessage = ChatMessage.createLoadingMessage();
        adapter.addMessage(loadingMessage);

        recyclerView.scrollToPosition(adapter.getMessageCount() - 1);

        isSending = true;
        updateSendButtonState();
        etInput.setText("");

        TCMRequest request = new TCMRequest.Builder()
                .userId(currentProfile.getUserId())
                .userText(TextUtils.isEmpty(userText) ? null : userText)
                .tongueImage(tongueBase64)
                .faceImage(faceBase64)
                .savedContext(currentProfile.getSavedContext())
                .history(new ArrayList<>(currentProfile.getHistory()))
                .build();

        clearSelectedImages();

        TCMApiClient.getInstance().sendConsultation(request, new TCMApiClient.ApiCallback() {
            @Override
            public void onSuccess(TCMResponse response) {
                handleResponse(response);
            }

            @Override
            public void onError(String errorMessage) {
                handleError(errorMessage);
            }
        });
    }

    private void handleResponse(TCMResponse response) {
        adapter.removeLastMessage();

        String replyText = response.getReplyText();
        if (replyText == null || replyText.isEmpty()) {
            replyText = "抱歉，暂时无法获取回复";
        }

        ChatMessage assistantMessage = ChatMessage.createAssistantMessage(replyText);
        adapter.addMessage(assistantMessage);
        currentProfile.addAssistantMessage(replyText);

        Map<String, Object> newContext = response.getNewContext();
        if (newContext != null) {
            currentProfile.mergeSavedContext(newContext);
        }

        storage.updateProfile(currentProfile);
        recyclerView.scrollToPosition(adapter.getMessageCount() - 1);

        isSending = false;
        updateSendButtonState();
    }

    private void handleError(String errorMessage) {
        adapter.removeLastMessage();
        adapter.removeLastMessage();

        List<ChatMessage> history = currentProfile.getHistory();
        if (!history.isEmpty()) {
            history.remove(history.size() - 1);
            storage.updateProfile(currentProfile);
        }

        Toast.makeText(this, errorMessage, Toast.LENGTH_LONG).show();

        isSending = false;
        updateSendButtonState();
    }

    private void showHistoryLimitDialog() {
        new AlertDialog.Builder(this)
                .setTitle("对话轮数已达上限")
                .setMessage("当前对话已达到 " + Constants.MAX_HISTORY_ROUNDS + " 轮上限。请选择如何继续：")
                .setPositiveButton("保留关键信息开启新对话", (dialog, which) -> {
                    currentProfile.clearHistory();
                    storage.updateProfile(currentProfile);
                    adapter.setMessages(new ArrayList<>());
                    Toast.makeText(this, "已开启新对话，关键信息已保留", Toast.LENGTH_SHORT).show();
                })
                .setNegativeButton("清空所有信息开启新对话", (dialog, which) -> {
                    currentProfile.clearHistory();
                    currentProfile.clearSavedContext();
                    storage.updateProfile(currentProfile);
                    adapter.setMessages(new ArrayList<>());
                    Toast.makeText(this, "已开启全新对话", Toast.LENGTH_SHORT).show();
                })
                .setNeutralButton("取消", null)
                .show();
    }

    private void showImagePickerDialog(int imageType) {
        currentImageType = imageType;
        String title = imageType == Constants.IMAGE_TYPE_TONGUE ? "上传舌像" : "上传面像";

        new AlertDialog.Builder(this)
                .setTitle(title)
                .setItems(new String[]{"拍照", "从相册选择"}, (dialog, which) -> {
                    if (which == 0) {
                        checkCameraPermissionAndTakePhoto(imageType);
                    } else {
                        openGallery(imageType);
                    }
                })
                .show();
    }

    private void checkCameraPermissionAndTakePhoto(int imageType) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            currentImageType = imageType;
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA},
                    PERMISSION_REQUEST_CAMERA);
        } else {
            takePhoto(imageType);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CAMERA) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                takePhoto(currentImageType);
            } else {
                Toast.makeText(this, "需要相机权限才能拍照", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void takePhoto(int imageType) {
        try {
            File photoFile = createImageFile();
            if (photoFile != null) {
                Uri photoUri = FileProvider.getUriForFile(this,
                        getPackageName() + ".fileprovider", photoFile);

                if (imageType == Constants.IMAGE_TYPE_TONGUE) {
                    tongueCameraLauncher.launch(photoUri);
                } else {
                    faceCameraLauncher.launch(photoUri);
                }
            }
        } catch (IOException e) {
            Toast.makeText(this, "创建图片文件失败", Toast.LENGTH_SHORT).show();
        }
    }

    private File createImageFile() throws IOException {
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.CHINA).format(new Date());
        String imageFileName = "TCM_" + timeStamp + "_";

        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        File image = File.createTempFile(imageFileName, ".jpg", storageDir);

        currentPhotoPath = image.getAbsolutePath();
        return image;
    }

    private void openGallery(int imageType) {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        intent.setType("image/*");

        if (imageType == Constants.IMAGE_TYPE_TONGUE) {
            tongueGalleryLauncher.launch(intent);
        } else {
            faceGalleryLauncher.launch(intent);
        }
    }

    private void handleImageResult(Uri uri, int imageType) {
        if (uri == null) return;

        new Thread(() -> {
            String base64 = ImageUtils.uriToBase64(this, uri);
            runOnUiThread(() -> {
                if (base64 != null) {
                    if (imageType == Constants.IMAGE_TYPE_TONGUE) {
                        tongueBase64 = base64;
                        tongueUri = uri;
                        showTonguePreview(uri);
                    } else {
                        faceBase64 = base64;
                        faceUri = uri;
                        showFacePreview(uri);
                    }
                    updateSendButtonState();
                } else {
                    Toast.makeText(this, "图片处理失败", Toast.LENGTH_SHORT).show();
                }
            });
        }).start();
    }

    private void handleCameraResult(String filePath, int imageType) {
        new Thread(() -> {
            String base64 = ImageUtils.fileToBase64(filePath);
            Uri uri = Uri.fromFile(new File(filePath));
            runOnUiThread(() -> {
                if (base64 != null) {
                    if (imageType == Constants.IMAGE_TYPE_TONGUE) {
                        tongueBase64 = base64;
                        tongueUri = uri;
                        showTonguePreview(uri);
                    } else {
                        faceBase64 = base64;
                        faceUri = uri;
                        showFacePreview(uri);
                    }
                    updateSendButtonState();
                } else {
                    Toast.makeText(this, "图片处理失败", Toast.LENGTH_SHORT).show();
                }
            });
        }).start();
    }

    private void showTonguePreview(Uri uri) {
        layoutTonguePreview.setVisibility(View.VISIBLE);
        Glide.with(this).load(uri).centerCrop().into(ivTonguePreview);
    }

    private void showFacePreview(Uri uri) {
        layoutFacePreview.setVisibility(View.VISIBLE);
        Glide.with(this).load(uri).centerCrop().into(ivFacePreview);
    }

    private void removeTongueImage() {
        tongueBase64 = null;
        tongueUri = null;
        layoutTonguePreview.setVisibility(View.GONE);
        ivTonguePreview.setImageDrawable(null);
        updateSendButtonState();
    }

    private void removeFaceImage() {
        faceBase64 = null;
        faceUri = null;
        layoutFacePreview.setVisibility(View.GONE);
        ivFacePreview.setImageDrawable(null);
        updateSendButtonState();
    }

    private void clearSelectedImages() {
        removeTongueImage();
        removeFaceImage();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.menu_chat, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(@NonNull MenuItem item) {
        int id = item.getItemId();
        if (id == R.id.action_new_profile) {
            Intent intent = new Intent(this, ProfileEditActivity.class);
            startActivity(intent);
            return true;
        } else if (id == R.id.action_end_diagnosis) {
            Toast.makeText(this, "诊断记录已保存", Toast.LENGTH_SHORT).show();
            finish();
            return true;
        } else if (id == R.id.action_delete_diagnosis) {
            showDeleteConfirmDialog();
            return true;
        } else if (id == R.id.action_switch_profile) {
            Intent intent = new Intent(this, ProfileActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private void showDeleteConfirmDialog() {
        new AlertDialog.Builder(this)
                .setTitle("删除诊断记录")
                .setMessage("确定要删除当前问诊人的所有记录吗？此操作不可恢复。")
                .setPositiveButton("删除", (dialog, which) -> {
                    storage.deleteProfile(currentProfile.getUserId());
                    Toast.makeText(this, "已删除", Toast.LENGTH_SHORT).show();
                    finish();
                })
                .setNegativeButton("取消", null)
                .show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        TCMApiClient.getInstance().cancelAll();
    }
}
