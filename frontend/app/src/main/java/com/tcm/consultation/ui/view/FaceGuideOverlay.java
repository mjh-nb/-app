package com.tcm.consultation.ui.view;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.DashPathEffect;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.View;

import androidx.annotation.Nullable;

/**
 * 面像人脸引导框 - 简化为大椭圆版
 * 特点：黑色虚线椭圆、符合真实人脸比例（宽:高 ≈ 3:4）、居中、宽屏适配
 */
public class FaceGuideOverlay extends View {

    private Paint overlayPaint;
    private Paint borderPaint;
    private Paint clearPaint;
    private RectF faceOval;

    public FaceGuideOverlay(Context context) {
        super(context);
        init();
    }

    public FaceGuideOverlay(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public FaceGuideOverlay(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        setLayerType(LAYER_TYPE_SOFTWARE, null);

        overlayPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        overlayPaint.setColor(Color.parseColor("#95000000"));
        overlayPaint.setStyle(Paint.Style.FILL);

        borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        borderPaint.setColor(Color.BLACK);
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(6f);
        borderPaint.setPathEffect(new DashPathEffect(new float[]{20, 12}, 0));
        borderPaint.setStrokeCap(Paint.Cap.ROUND);

        clearPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        clearPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);

        // 椭圆宽度：占屏幕 88%
        float ovalWidth = w * 0.88f;
        // 人脸比例：宽:高 = 3:4 → 高 = 宽 / 0.75
        float ovalHeight = ovalWidth / 0.75f;

        // 居中计算
        float left = (w - ovalWidth) / 2f;
        float top = (h - ovalHeight) / 2f;
        float right = left + ovalWidth;
        float bottom = top + ovalHeight;

        faceOval = new RectF(left, top, right, bottom);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (faceOval == null) return;

        // 1. 绘制半透明遮罩
        canvas.drawRect(0, 0, getWidth(), getHeight(), overlayPaint);

        // 2. 镂空椭圆区域（内部透明）
        canvas.drawOval(faceOval, clearPaint);

        // 3. 绘制黑色虚线边框
        canvas.drawOval(faceOval, borderPaint);
    }

    public RectF getGuideRect() {
        return faceOval;
    }
}