package com.tcm.consultation.ui;

import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.tcm.consultation.R;
import com.tcm.consultation.ui.view.CropImageView;
import com.tcm.consultation.ui.view.FaceGuideOverlay;
import com.tcm.consultation.ui.view.TongueGuideOverlay;
import com.tcm.consultation.utils.Constants;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * 图片裁剪页面
 * 支持缩放、平移，将有效区域裁剪后返回
 * 舌像和面像使用相同大小的引导框
 */
public class ImageCropActivity extends AppCompatActivity {

    public static final String EXTRA_IMAGE_URI = "extra_image_uri";
    public static final String EXTRA_IMAGE_TYPE = "extra_image_type";
    public static final String EXTRA_CROPPED_URI = "extra_cropped_uri";

    private CropImageView cropImageView;
    private TongueGuideOverlay tongueGuide;
    private FaceGuideOverlay faceGuide;
    private int imageType;
    private Uri sourceUri;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_image_crop);

        sourceUri = getIntent().getParcelableExtra(EXTRA_IMAGE_URI);
        imageType = getIntent().getIntExtra(EXTRA_IMAGE_TYPE, Constants.IMAGE_TYPE_TONGUE);

        initViews();
        loadImage();
    }

    private void initViews() {
        cropImageView = findViewById(R.id.crop_image_view);
        tongueGuide = findViewById(R.id.tongue_guide_overlay);
        faceGuide = findViewById(R.id.face_guide_overlay);
        Button btnConfirm = findViewById(R.id.btn_confirm);
        Button btnCancel = findViewById(R.id.btn_cancel);
        ImageButton btnReset = findViewById(R.id.btn_reset);
        TextView tvTitle = findViewById(R.id.tv_title);
        TextView tvHint = findViewById(R.id.tv_hint);

        // 根据类型显示不同引导框和提示
        if (imageType == Constants.IMAGE_TYPE_TONGUE) {
            tongueGuide.setVisibility(View.VISIBLE);
            faceGuide.setVisibility(View.GONE);
            tvTitle.setText("调整舌像位置");
            tvHint.setText("请将舌头移入椭圆框内\n双指缩放，单指拖动，双击重置");
        } else {
            tongueGuide.setVisibility(View.GONE);
            faceGuide.setVisibility(View.VISIBLE);
            tvTitle.setText("调整面像位置");
            tvHint.setText("请将面部移入引导框内\n双指缩放，单指拖动，双击重置");
        }

        btnConfirm.setOnClickListener(v -> cropAndReturn());
        btnCancel.setOnClickListener(v -> {
            setResult(RESULT_CANCELED);
            finish();
        });
        
        // 重置按钮
        btnReset.setOnClickListener(v -> {
            cropImageView.resetImage();
            Toast.makeText(this, "已重置", Toast.LENGTH_SHORT).show();
        });
    }

    private void loadImage() {
        if (sourceUri != null) {
            cropImageView.setImageUri(sourceUri);
        }
    }

    private void cropAndReturn() {
        try {
            // 获取裁剪后的图片
            View guideView = (imageType == Constants.IMAGE_TYPE_TONGUE) ? tongueGuide : faceGuide;
            Bitmap croppedBitmap = cropImageView.getCroppedBitmap(guideView);

            if (croppedBitmap == null) {
                Toast.makeText(this, "裁剪失败，请重试", Toast.LENGTH_SHORT).show();
                return;
            }

            // 保存裁剪后的图片
            File outputFile = createTempFile();
            FileOutputStream fos = new FileOutputStream(outputFile);
            croppedBitmap.compress(Bitmap.CompressFormat.JPEG, 90, fos);
            fos.close();
            croppedBitmap.recycle();

            Uri resultUri = Uri.fromFile(outputFile);

            Intent resultIntent = new Intent();
            resultIntent.putExtra(EXTRA_CROPPED_URI, resultUri);
            setResult(RESULT_OK, resultIntent);
            finish();

        } catch (IOException e) {
            Toast.makeText(this, "保存图片失败", Toast.LENGTH_SHORT).show();
        }
    }

    private File createTempFile() throws IOException {
        File cacheDir = getCacheDir();
        return File.createTempFile("cropped_", ".jpg", cacheDir);
    }
}
