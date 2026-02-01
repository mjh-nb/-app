package com.tcm.consultation.ui;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.google.common.util.concurrent.ListenableFuture;
import com.tcm.consultation.R;
import com.tcm.consultation.utils.Constants;

import java.io.File;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutionException;

/**
 * 自定义相机Activity
 * 带有引导框提示用户拍摄位置
 * 修正：默认前置摄像头，支持前后置切换，修复前置摄像头镜像问题
 */
public class CustomCameraActivity extends AppCompatActivity {

    public static final String EXTRA_IMAGE_TYPE = "extra_image_type";
    public static final String EXTRA_PHOTO_URI = "extra_photo_uri";

    private static final int PERMISSION_CAMERA = 101;

    private PreviewView previewView;
    private ImageCapture imageCapture;
    private int imageType;

    // 摄像头相关
    private boolean isFrontCamera = true;  // 默认前置摄像头
    private ProcessCameraProvider cameraProvider;
    private ImageButton btnSwitchCamera;

    private ActivityResultLauncher<Intent> cropLauncher;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_custom_camera);

        imageType = getIntent().getIntExtra(EXTRA_IMAGE_TYPE, Constants.IMAGE_TYPE_TONGUE);

        initCropLauncher();
        initViews();
        checkPermissionAndStartCamera();
    }

    private void initCropLauncher() {
        cropLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        Uri croppedUri = result.getData().getParcelableExtra(
                                ImageCropActivity.EXTRA_CROPPED_URI);
                        Intent resultIntent = new Intent();
                        resultIntent.putExtra(EXTRA_PHOTO_URI, croppedUri);
                        resultIntent.putExtra(EXTRA_IMAGE_TYPE, imageType);
                        setResult(RESULT_OK, resultIntent);
                    }
                    finish();
                });
    }

    private void initViews() {
        previewView = findViewById(R.id.preview_view);
        View tongueGuide = findViewById(R.id.tongue_guide_overlay);
        View faceGuide = findViewById(R.id.face_guide_overlay);
        ImageButton btnCapture = findViewById(R.id.btn_capture);
        ImageButton btnClose = findViewById(R.id.btn_close);
        btnSwitchCamera = findViewById(R.id.btn_switch_camera);
        TextView tvHint = findViewById(R.id.tv_hint);

        // 显示对应的引导框和提示
        if (imageType == Constants.IMAGE_TYPE_TONGUE) {
            tongueGuide.setVisibility(View.VISIBLE);
            faceGuide.setVisibility(View.GONE);
            tvHint.setText("请将舌头对准椭圆引导框");
        } else {
            tongueGuide.setVisibility(View.GONE);
            faceGuide.setVisibility(View.VISIBLE);
            tvHint.setText("请将面部对准引导框");
        }

        btnCapture.setOnClickListener(v -> takePhoto());
        btnClose.setOnClickListener(v -> {
            setResult(RESULT_CANCELED);
            finish();
        });

        // 切换摄像头按钮
        btnSwitchCamera.setOnClickListener(v -> switchCamera());
    }

    private void checkPermissionAndStartCamera() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED) {
            startCamera();
        } else {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA}, PERMISSION_CAMERA);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_CAMERA) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startCamera();
            } else {
                Toast.makeText(this, "需要相机权限", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> cameraProviderFuture =
                ProcessCameraProvider.getInstance(this);

        cameraProviderFuture.addListener(() -> {
            try {
                cameraProvider = cameraProviderFuture.get();
                bindCamera();
            } catch (ExecutionException | InterruptedException e) {
                Toast.makeText(this, "相机启动失败", Toast.LENGTH_SHORT).show();
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void bindCamera() {
        if (cameraProvider == null) return;

        Preview preview = new Preview.Builder().build();
        preview.setSurfaceProvider(previewView.getSurfaceProvider());

        imageCapture = new ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                .build();

        // 根据 isFrontCamera 选择摄像头，默认前置
        CameraSelector cameraSelector = isFrontCamera
                ? CameraSelector.DEFAULT_FRONT_CAMERA
                : CameraSelector.DEFAULT_BACK_CAMERA;

        try {
            cameraProvider.unbindAll();
            cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageCapture);
        } catch (Exception e) {
            // 如果选择的摄像头不可用，尝试另一个
            try {
                cameraSelector = isFrontCamera
                        ? CameraSelector.DEFAULT_BACK_CAMERA
                        : CameraSelector.DEFAULT_FRONT_CAMERA;
                isFrontCamera = !isFrontCamera;
                cameraProvider.unbindAll();
                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageCapture);
            } catch (Exception e2) {
                Toast.makeText(this, "无法启动相机", Toast.LENGTH_SHORT).show();
            }
        }
    }

    //切换前后摄像头
    private void switchCamera() {
        isFrontCamera = !isFrontCamera;
        bindCamera();

        // 显示提示
        String cameraName = isFrontCamera ? "前置摄像头" : "后置摄像头";
        Toast.makeText(this, "已切换到" + cameraName, Toast.LENGTH_SHORT).show();
    }

    private void takePhoto() {
        if (imageCapture == null) return;

        File photoFile = createPhotoFile();
        ImageCapture.OutputFileOptions outputOptions =
                new ImageCapture.OutputFileOptions.Builder(photoFile).build();

        imageCapture.takePicture(outputOptions, ContextCompat.getMainExecutor(this),
                new ImageCapture.OnImageSavedCallback() {
                    @Override
                    public void onImageSaved(@NonNull ImageCapture.OutputFileResults output) {
                        // 如果是前置摄像头，需要镜像翻转图片
                        if (isFrontCamera) {
                            flipImageHorizontally(photoFile);
                        }

                        Uri savedUri = Uri.fromFile(photoFile);

                        // 跳转到裁剪页面
                        Intent cropIntent = new Intent(CustomCameraActivity.this,
                                ImageCropActivity.class);
                        cropIntent.putExtra(ImageCropActivity.EXTRA_IMAGE_URI, savedUri);
                        cropIntent.putExtra(ImageCropActivity.EXTRA_IMAGE_TYPE, imageType);
                        cropLauncher.launch(cropIntent);
                    }

                    @Override
                    public void onError(@NonNull ImageCaptureException exception) {
                        Toast.makeText(CustomCameraActivity.this,
                                "拍照失败", Toast.LENGTH_SHORT).show();
                    }
                });
    }

    //水平翻转图片（解决前置摄像头镜像问题）
    private void flipImageHorizontally(File imageFile) {
        try {
            Bitmap original = BitmapFactory.decodeFile(imageFile.getAbsolutePath());
            if (original == null) return;

            Matrix matrix = new Matrix();
            matrix.preScale(-1.0f, 1.0f);  // 水平翻转

            Bitmap flipped = Bitmap.createBitmap(original, 0, 0,
                    original.getWidth(), original.getHeight(), matrix, true);

            // 保存翻转后的图片
            FileOutputStream fos = new FileOutputStream(imageFile);
            flipped.compress(Bitmap.CompressFormat.JPEG, 90, fos);
            fos.close();

            // 回收bitmap
            if (flipped != original) {
                original.recycle();
            }
            flipped.recycle();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private File createPhotoFile() {
        String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.CHINA).format(new Date());
        File storageDir = getExternalFilesDir(null);
        return new File(storageDir, "TCM_" + timestamp + ".jpg");
    }
}
