package com.tcm.consultation.utils;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.net.Uri;
import android.util.Base64;

import androidx.exifinterface.media.ExifInterface;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

/**
 * ImageUtils - 图片处理工具类
 * 职责：图片压缩、旋转校正、Base64 编码等操作
 */
public final class ImageUtils {

    private ImageUtils() {
        // 防止实例化
    }

    /**
     * 从 Uri 加载图片并压缩转换为 Base64 字符串
     * 
     * @param context 上下文
     * @param uri     图片 Uri
     * @return Base64 编码字符串（不含前缀）
     */
    public static String uriToBase64(Context context, Uri uri) {
        try {
            // 读取图片尺寸
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;

            InputStream inputStream = context.getContentResolver().openInputStream(uri);
            BitmapFactory.decodeStream(inputStream, null, options);
            if (inputStream != null) {
                inputStream.close();
            }

            // 计算采样率
            options.inSampleSize = calculateInSampleSize(options,
                    Constants.IMAGE_MAX_WIDTH, Constants.IMAGE_MAX_HEIGHT);
            options.inJustDecodeBounds = false;

            // 解码图片
            inputStream = context.getContentResolver().openInputStream(uri);
            Bitmap bitmap = BitmapFactory.decodeStream(inputStream, null, options);
            if (inputStream != null) {
                inputStream.close();
            }

            if (bitmap == null) {
                return null;
            }

            // 校正图片旋转
            bitmap = correctRotation(context, uri, bitmap);

            // 缩放图片
            bitmap = scaleBitmap(bitmap, Constants.IMAGE_MAX_WIDTH, Constants.IMAGE_MAX_HEIGHT);

            // 压缩为 JPEG 并转换为 Base64
            return bitmapToBase64(bitmap);

        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * 计算采样率
     */
    private static int calculateInSampleSize(BitmapFactory.Options options,
                                              int reqWidth, int reqHeight) {
        int height = options.outHeight;
        int width = options.outWidth;
        int inSampleSize = 1;

        if (height > reqHeight || width > reqWidth) {
            int halfHeight = height / 2;
            int halfWidth = width / 2;

            while ((halfHeight / inSampleSize) >= reqHeight
                    && (halfWidth / inSampleSize) >= reqWidth) {
                inSampleSize *= 2;
            }
        }

        return inSampleSize;
    }

    /**
     * 校正图片旋转角度（根据 EXIF 信息）
     */
    private static Bitmap correctRotation(Context context, Uri uri, Bitmap bitmap) {
        try {
            InputStream inputStream = context.getContentResolver().openInputStream(uri);
            if (inputStream == null) {
                return bitmap;
            }

            ExifInterface exif = new ExifInterface(inputStream);
            int orientation = exif.getAttributeInt(
                    ExifInterface.TAG_ORIENTATION,
                    ExifInterface.ORIENTATION_NORMAL);
            inputStream.close();

            int rotation = 0;
            switch (orientation) {
                case ExifInterface.ORIENTATION_ROTATE_90:
                    rotation = 90;
                    break;
                case ExifInterface.ORIENTATION_ROTATE_180:
                    rotation = 180;
                    break;
                case ExifInterface.ORIENTATION_ROTATE_270:
                    rotation = 270;
                    break;
            }

            if (rotation != 0) {
                Matrix matrix = new Matrix();
                matrix.postRotate(rotation);
                Bitmap rotated = Bitmap.createBitmap(bitmap, 0, 0,
                        bitmap.getWidth(), bitmap.getHeight(), matrix, true);
                if (rotated != bitmap) {
                    bitmap.recycle();
                }
                return rotated;
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

        return bitmap;
    }

    /**
     * 缩放图片到指定最大尺寸
     */
    private static Bitmap scaleBitmap(Bitmap bitmap, int maxWidth, int maxHeight) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();

        if (width <= maxWidth && height <= maxHeight) {
            return bitmap;
        }

        float scale = Math.min(
                (float) maxWidth / width,
                (float) maxHeight / height);

        int newWidth = Math.round(width * scale);
        int newHeight = Math.round(height * scale);

        Bitmap scaled = Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true);
        if (scaled != bitmap) {
            bitmap.recycle();
        }

        return scaled;
    }

    /**
     * Bitmap 转换为 Base64 字符串
     */
    private static String bitmapToBase64(Bitmap bitmap) {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, Constants.IMAGE_QUALITY, outputStream);
        byte[] bytes = outputStream.toByteArray();
        bitmap.recycle();

        return Base64.encodeToString(bytes, Base64.NO_WRAP);
    }

    /**
     * 从文件路径加载图片并转换为 Base64
     */
    public static String fileToBase64(String filePath) {
        try {
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            BitmapFactory.decodeFile(filePath, options);

            options.inSampleSize = calculateInSampleSize(options,
                    Constants.IMAGE_MAX_WIDTH, Constants.IMAGE_MAX_HEIGHT);
            options.inJustDecodeBounds = false;

            Bitmap bitmap = BitmapFactory.decodeFile(filePath, options);
            if (bitmap == null) {
                return null;
            }

            // 校正旋转
            try {
                ExifInterface exif = new ExifInterface(filePath);
                int orientation = exif.getAttributeInt(
                        ExifInterface.TAG_ORIENTATION,
                        ExifInterface.ORIENTATION_NORMAL);

                int rotation = 0;
                switch (orientation) {
                    case ExifInterface.ORIENTATION_ROTATE_90:
                        rotation = 90;
                        break;
                    case ExifInterface.ORIENTATION_ROTATE_180:
                        rotation = 180;
                        break;
                    case ExifInterface.ORIENTATION_ROTATE_270:
                        rotation = 270;
                        break;
                }

                if (rotation != 0) {
                    Matrix matrix = new Matrix();
                    matrix.postRotate(rotation);
                    Bitmap rotated = Bitmap.createBitmap(bitmap, 0, 0,
                            bitmap.getWidth(), bitmap.getHeight(), matrix, true);
                    if (rotated != bitmap) {
                        bitmap.recycle();
                    }
                    bitmap = rotated;
                }
            } catch (IOException e) {
                e.printStackTrace();
            }

            bitmap = scaleBitmap(bitmap, Constants.IMAGE_MAX_WIDTH, Constants.IMAGE_MAX_HEIGHT);
            return bitmapToBase64(bitmap);

        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}
