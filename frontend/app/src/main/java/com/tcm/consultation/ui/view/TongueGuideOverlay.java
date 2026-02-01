package com.tcm.consultation.ui.view;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.DashPathEffect;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.View;

import androidx.annotation.Nullable;

/**
 * 舌像椭圆引导框
 * 绘制半透明遮罩，中间留出椭圆形透明区域
 * 修正：更大、更圆的椭圆比例
 */
public class TongueGuideOverlay extends View {

    private Paint overlayPaint;
    private Paint borderPaint;
    private Paint clearPaint;
    private RectF ovalRect;

    public TongueGuideOverlay(Context context) {
        super(context);
        init();
    }

    public TongueGuideOverlay(Context context, @Nullable AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public TongueGuideOverlay(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        setLayerType(LAYER_TYPE_SOFTWARE, null);

        // 半透明遮罩画笔
        overlayPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        overlayPaint.setColor(Color.parseColor("#80000000"));
        overlayPaint.setStyle(Paint.Style.FILL);

        // 椭圆边框画笔（虚线）- 加粗
        borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        borderPaint.setColor(Color.BLACK);
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(6f);  // 加粗线条
        borderPaint.setPathEffect(new DashPathEffect(new float[]{30, 20}, 0));  // 更明显的虚线

        // 清除画笔
        clearPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        clearPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);

        // 修正：更大、更圆的椭圆（参考图2的比例）
        // 宽度占屏幕 75%，高度略大于宽度形成竖椭圆
        float ovalWidth = w * 0.75f;
        float ovalHeight = ovalWidth * 1.2f;  // 高度是宽度的1.2倍，更接近圆形
        
        // 确保不超出屏幕
        if (ovalHeight > h * 0.7f) {
            ovalHeight = h * 0.7f;
            ovalWidth = ovalHeight / 1.2f;
        }
        
        float left = (w - ovalWidth) / 2f;
        float top = (h - ovalHeight) / 2f;

        ovalRect = new RectF(left, top, left + ovalWidth, top + ovalHeight);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        if (ovalRect == null) return;

        // 绘制半透明遮罩
        canvas.drawRect(0, 0, getWidth(), getHeight(), overlayPaint);

        // 清除椭圆区域
        canvas.drawOval(ovalRect, clearPaint);

        // 绘制虚线边框
        canvas.drawOval(ovalRect, borderPaint);
    }

    //获取引导框区域
    public RectF getGuideRect() {
        return ovalRect;
    }
}
