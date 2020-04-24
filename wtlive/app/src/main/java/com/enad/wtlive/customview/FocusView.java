package com.enad.wtlive.customview;

import android.content.Context;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.BitmapDrawable;
import android.util.AttributeSet;
import android.view.View;
import com.enad.wtlive.R;
import com.enad.wtlive.env.Logger;

public class FocusView extends View {
    private int ratioWidth = 0;
    private int ratioHeight = 0;
    private static final Logger LOGGER = new Logger();
    private String prediction = "";
    private float confidence = 0.0f;

    boolean normal = true;
    Paint paint;
    int w = 0;
    float minLeft = 0.0f;
    float minTop = 0.0f;

    public FocusView(final Context context) {
        this(context, null);
        paint = new Paint();
    }

    public FocusView(final Context context, AttributeSet attrs) {
        this(context, attrs, 0);
        paint = new Paint();
    }

    public FocusView(final Context context, final AttributeSet attrs, final int defStyle) {
        super(context, attrs, defStyle);
        paint = new Paint();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        if (normal) drawTitle(canvas);
        drawFocus(canvas);
    }

    @Override
    protected void onMeasure(final int widthMeasureSpec, final int heightMeasureSpec) {
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
        final int width = MeasureSpec.getSize(widthMeasureSpec);
        final int height = MeasureSpec.getSize(heightMeasureSpec);

        if (0 == ratioWidth || 0 == ratioHeight) {
            setMeasuredDimension(width, height);
            LOGGER.d("check 0: " + "width=" + width + " height=" + height);
        } else {
            if (width < height * ratioWidth / ratioHeight) {
                setMeasuredDimension(width, width * ratioHeight / ratioWidth);
                minTop = (width * ratioHeight / ratioWidth - width)/2;
                w = width;
                normal = true;
                LOGGER.d("check 1: " + "width=" + width + " ratioHeight = " + ratioHeight + " ratioWidth=" + ratioWidth +
                        " width * ratioHeight / ratioWidth=" + width * ratioHeight / ratioWidth);
                //LOGGER.d("check 1: " + "width=" + width + " width * ratioHeight / ratioWidth=" + width * ratioHeight / ratioWidth);
            } else {
                setMeasuredDimension(height * ratioWidth / ratioHeight, height);
                minLeft = (height * ratioWidth / ratioHeight - height)/2;
                w = height;
                normal = false;
                LOGGER.d("check 2: " + "height * ratioWidth / ratioHeight=" + height * ratioWidth / ratioHeight + " height=" + height);
            }
        }
    }

    public void setAspectRatio(final int width, final int height) {
        if (width < 0 || height < 0) {
            throw new IllegalArgumentException("Size cannot be negative.");
        }
        ratioWidth = width;
        ratioHeight = height;
        requestLayout();
    }

    protected void drawFocus(Canvas c) {
        paint.setStyle(Paint.Style.STROKE);
        paint.setARGB(255, 142, 198, 65); // some green
        paint.setAlpha(255);
        paint.setStrokeWidth(w*0.02f); // anchor width

        /* draw image frame */
        float L = minLeft, R = minLeft+w, T = minTop, D = minTop+w, CX = L+w/2, CY = T+w/2;
        float a = w*0.1f; // anchor length
        float[] anchor= {L, T, L+a,T,
                L, T, L, T+a,
                R, T, R-a, T,
                R, T, R, T+a,
                L, D, L+a, D,
                L, D, L, D-a,
                R, D, R-a, D,
                R, D, R, D-a};
        c.drawLines(anchor, paint);

        /* draw front sight */
        paint.setAlpha(50);
        c.drawCircle(CX, CY, a, paint);
        float[] cross = {CX-a*0.7f, CY, CX+a*0.7f, CY,
                CX, CY-a*0.7f, CX, CY+a*0.7f};
        c.drawLines(cross, paint);
    }

    protected void drawTitle(Canvas c) {
        paint.setAlpha(255);

        /* draw back ground */
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(Color.BLACK);
        c.drawRect(0, 0, w, minTop, paint);
        c.drawRect(0, minTop+w, w, minTop*2+w, paint);

        /* draw icon */
        Resources resources = this.getResources();
        BitmapDrawable iconDrawable = (BitmapDrawable) resources.getDrawable(R.drawable.wt_icon_nobg);
        Bitmap iconBitmap = iconDrawable.getBitmap();
        float r = minTop*0.9f, b = minTop*0.9f;
        RectF RR = new RectF(0, 0, r, b);
        c.drawBitmap(iconBitmap, null, RR, paint);

        /* draw APP name */
        float s = minTop*0.5f; // size of text, to avoid cover camera
        paint.setTextSize(s);
        paint.setARGB(255, 157, 100, 57); // some brown
        String title = resources.getString(R.string.activity_name_classification);
        c.drawText(title, r + w*0.05f, s + (minTop-s)/2, paint);

        /* draw prediction */
        paint.setTextSize(s);
        paint.setARGB((int)(255 * confidence), 142, 198, 65); // some green
        c.drawText(prediction, r + w*0.1f + s * title.length(), s + (minTop-s)/2, paint);
    }

    public void setPrediction(String pred, float conf) {
        prediction = (pred == null) ? "" : pred;
        confidence = conf;
        invalidate();
    }
}
