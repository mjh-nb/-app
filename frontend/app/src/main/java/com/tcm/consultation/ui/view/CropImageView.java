package com.tcm.consultation.ui.view;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Matrix;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.util.AttributeSet;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.View;

import androidx.annotation.Nullable;
import androidx.appcompat.widget.AppCompatImageView;

import com.bumptech.glide.Glide;
import com.bumptech.glide.request.target.CustomTarget;
import com.bumptech.glide.request.transition.Transition;

/**
 * 可缩放、平移的图片视图
 * 用于图片裁剪功能
 * 修正：确保支持缩放和滑动
 */
public class CropImageView extends AppCompatImageView {

    private Matrix imageMatrix = new Matrix();
    private float[] matrixValues = new float[9];

    private ScaleGestureDetector scaleDetector;
    private GestureDetector gestureDetector;

    private float minScale = 0.3f;
    private float maxScale = 10.0f;
    private float currentScale = 1.0f;
    private float baseScale = 1.0f;

    private Bitmap currentBitmap;
    private boolean isInitialized = false;

    // 多点触控相关
    private float lastTouchX;
    private float lastTouchY;
    private int activePointerId = -1;
    private boolean isScaling = false;

    public CropImageView(Context context) {
        super(context);
        init(context);
    }

    public CropImageView(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init(context);
    }

    public CropImageView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init(context);
    }

    private void init(Context context) {
        setScaleType(ScaleType.MATRIX);

        scaleDetector = new ScaleGestureDetector(context, new ScaleListener());
        gestureDetector = new GestureDetector(context, new GestureListener());
    }

    public void setImageUri(Uri uri) {
        Glide.with(getContext())
                .asBitmap()
                .load(uri)
                .into(new CustomTarget<Bitmap>() {
                    @Override
                    public void onResourceReady(Bitmap resource, Transition<? super Bitmap> transition) {
                        currentBitmap = resource;
                        setImageBitmap(resource);
                        post(() -> centerAndFitImage());
                    }

                    @Override
                    public void onLoadCleared(@Nullable Drawable placeholder) {
                    }
                });
    }

    private void centerAndFitImage() {
        if (currentBitmap == null) return;

        int viewWidth = getWidth();
        int viewHeight = getHeight();

        if (viewWidth == 0 || viewHeight == 0) return;

        int bitmapWidth = currentBitmap.getWidth();
        int bitmapHeight = currentBitmap.getHeight();

        // 使用 max 确保图片填满区域
        float scaleX = (float) viewWidth / bitmapWidth;
        float scaleY = (float) viewHeight / bitmapHeight;
        float scale = Math.max(scaleX, scaleY);

        imageMatrix.reset();
        imageMatrix.postScale(scale, scale);

        float translateX = (viewWidth - bitmapWidth * scale) / 2f;
        float translateY = (viewHeight - bitmapHeight * scale) / 2f;
        imageMatrix.postTranslate(translateX, translateY);

        setImageMatrix(imageMatrix);
        currentScale = scale;
        baseScale = scale;
        minScale = scale * 0.5f;
        maxScale = scale * 5.0f;
        isInitialized = true;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (!isInitialized || currentBitmap == null) return true;

        // 处理缩放手势
        scaleDetector.onTouchEvent(event);
        
        // 如果不在缩放状态，处理滑动
        if (!scaleDetector.isInProgress()) {
            handleDragEvent(event);
        }

        return true;
    }

    private void handleDragEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                activePointerId = event.getPointerId(0);
                lastTouchX = event.getX();
                lastTouchY = event.getY();
                break;

            case MotionEvent.ACTION_MOVE:
                if (activePointerId != -1 && !scaleDetector.isInProgress()) {
                    int pointerIndex = event.findPointerIndex(activePointerId);
                    if (pointerIndex != -1) {
                        float x = event.getX(pointerIndex);
                        float y = event.getY(pointerIndex);

                        float dx = x - lastTouchX;
                        float dy = y - lastTouchY;

                        imageMatrix.postTranslate(dx, dy);
                        setImageMatrix(imageMatrix);

                        lastTouchX = x;
                        lastTouchY = y;
                    }
                }
                break;

            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                activePointerId = -1;
                break;

            case MotionEvent.ACTION_POINTER_UP:
                int pointerIndex = event.getActionIndex();
                int pointerId = event.getPointerId(pointerIndex);
                if (pointerId == activePointerId) {
                    int newPointerIndex = pointerIndex == 0 ? 1 : 0;
                    if (newPointerIndex < event.getPointerCount()) {
                        lastTouchX = event.getX(newPointerIndex);
                        lastTouchY = event.getY(newPointerIndex);
                        activePointerId = event.getPointerId(newPointerIndex);
                    } else {
                        activePointerId = -1;
                    }
                }
                break;
        }
    }

    /**
     * 获取裁剪后的图片
     */
    public Bitmap getCroppedBitmap(View guideView) {
        if (currentBitmap == null) return null;

        try {
            // 创建一个与视图大小相同的Bitmap
            Bitmap viewBitmap = Bitmap.createBitmap(getWidth(), getHeight(), Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(viewBitmap);
            draw(canvas);

            // 获取引导框在视图中的位置
            int[] guideLocation = new int[2];
            int[] viewLocation = new int[2];
            guideView.getLocationOnScreen(guideLocation);
            getLocationOnScreen(viewLocation);

            int left = guideLocation[0] - viewLocation[0];
            int top = guideLocation[1] - viewLocation[1];
            int width = guideView.getWidth();
            int height = guideView.getHeight();

            // 确保不超出边界
            left = Math.max(0, left);
            top = Math.max(0, top);
            width = Math.min(width, viewBitmap.getWidth() - left);
            height = Math.min(height, viewBitmap.getHeight() - top);

            if (width <= 0 || height <= 0) {
                return viewBitmap;
            }

            Bitmap cropped = Bitmap.createBitmap(viewBitmap, left, top, width, height);
            viewBitmap.recycle();
            return cropped;

        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * 重置到初始状态
     */
    public void resetImage() {
        centerAndFitImage();
    }

    private class ScaleListener extends ScaleGestureDetector.SimpleOnScaleGestureListener {
        @Override
        public boolean onScaleBegin(ScaleGestureDetector detector) {
            isScaling = true;
            return true;
        }

        @Override
        public boolean onScale(ScaleGestureDetector detector) {
            float scaleFactor = detector.getScaleFactor();
            float newScale = currentScale * scaleFactor;

            if (newScale >= minScale && newScale <= maxScale) {
                imageMatrix.postScale(scaleFactor, scaleFactor,
                        detector.getFocusX(), detector.getFocusY());
                setImageMatrix(imageMatrix);
                currentScale = newScale;
            }
            return true;
        }

        @Override
        public void onScaleEnd(ScaleGestureDetector detector) {
            isScaling = false;
        }
    }

    private class GestureListener extends GestureDetector.SimpleOnGestureListener {
        @Override
        public boolean onDoubleTap(MotionEvent e) {
            // 双击重置
            centerAndFitImage();
            return true;
        }
    }
}
