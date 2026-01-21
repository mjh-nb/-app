package com.tcm.consultation.ui;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import com.tcm.consultation.R;
import com.tcm.consultation.model.Profile;
import com.tcm.consultation.storage.ProfileStorage;
import com.tcm.consultation.utils.Constants;
import com.tcm.consultation.utils.UUIDUtils;

/**
 * ProfileEditActivity - 创建/编辑问诊人页
 * 职责：收集问诊人基本信息（姓名、性别、年龄）
 */
public class ProfileEditActivity extends AppCompatActivity {

    private EditText etName;
    private Spinner spinnerGender;
    private EditText etAge;
    private ProfileStorage storage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_profile_edit);

        storage = ProfileStorage.getInstance(this);

        initToolbar();
        initViews();
    }

    private void initToolbar() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle("新建问诊人");
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        toolbar.setNavigationOnClickListener(v -> onBackPressed());
    }

    private void initViews() {
        etName = findViewById(R.id.et_name);
        spinnerGender = findViewById(R.id.spinner_gender);
        etAge = findViewById(R.id.et_age);
        Button btnConfirm = findViewById(R.id.btn_confirm);

        // 设置性别选项
        String[] genderOptions = {Constants.GENDER_MALE, Constants.GENDER_FEMALE, Constants.GENDER_OTHER};
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, genderOptions);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerGender.setAdapter(adapter);

        // 确认按钮
        btnConfirm.setOnClickListener(v -> saveProfile());
    }

    private void saveProfile() {
        String name = etName.getText().toString().trim();
        String gender = spinnerGender.getSelectedItem().toString();
        String ageStr = etAge.getText().toString().trim();

        // 验证输入
        if (TextUtils.isEmpty(name)) {
            Toast.makeText(this, "请输入姓名", Toast.LENGTH_SHORT).show();
            etName.requestFocus();
            return;
        }

        if (TextUtils.isEmpty(ageStr)) {
            Toast.makeText(this, "请输入年龄", Toast.LENGTH_SHORT).show();
            etAge.requestFocus();
            return;
        }

        int age;
        try {
            age = Integer.parseInt(ageStr);
            if (age < 1 || age > 150) {
                Toast.makeText(this, "请输入有效的年龄", Toast.LENGTH_SHORT).show();
                etAge.requestFocus();
                return;
            }
        } catch (NumberFormatException e) {
            Toast.makeText(this, "年龄格式错误", Toast.LENGTH_SHORT).show();
            etAge.requestFocus();
            return;
        }

        // 创建新的问诊人档案
        String userId = UUIDUtils.generateProfileId();
        Profile profile = new Profile(userId, name, gender, age);

        // 保存到本地存储
        storage.addProfile(profile);

        // 设置为当前选中的问诊人
        storage.setCurrentProfileId(userId);

        Toast.makeText(this, "创建成功", Toast.LENGTH_SHORT).show();

        // 跳转到聊天页
        Intent intent = new Intent(this, ChatActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(intent);
        finish();
    }
}
