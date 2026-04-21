<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>AI 教学系统登录</h2>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="form" label-width="80px">
            <el-form-item label="登录身份">
              <el-radio-group v-model="form.loginMode">
                <el-radio-button label="student">学生登录</el-radio-button>
                <el-radio-button label="teacher">教师登录</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.username" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="loading" class="w-100">
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="学生注册" name="register">
          <el-form :model="registerForm" label-width="80px">
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" placeholder="请输入学生邮箱" />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="registerForm.fullName" placeholder="可选" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="至少6位"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="再次输入密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="success" @click="handleRegister" :loading="registering" class="w-100">
                注册学生账号
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const registering = ref(false)
const activeTab = ref('login')

const form = reactive({
  loginMode: 'student',
  username: '',
  password: '',
})

const registerForm = reactive({
  email: '',
  fullName: '',
  password: '',
  confirmPassword: '',
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入邮箱和密码')
    return
  }

  loading.value = true
  const success = await authStore.login(form.username, form.password)
  loading.value = false

  if (success) {
    const role = authStore.user?.role || ''
    const asStudent = form.loginMode === 'student'
    const isTeacherRole = role === 'instructor' || role === 'admin'
    const isStudentRole = role === 'student'

    if ((asStudent && !isStudentRole) || (!asStudent && !isTeacherRole)) {
      authStore.logout()
      ElMessage.error('登录身份与账号角色不匹配，请切换身份后重试')
      return
    }

    ElMessage.success('登录成功')
    if (isTeacherRole) {
      router.push('/teacher')
    } else {
      router.push('/')
    }
  } else {
    ElMessage.error('登录失败，请检查用户名或密码')
  }
}

const handleRegister = async () => {
  if (!registerForm.email || !registerForm.password || !registerForm.confirmPassword) {
    ElMessage.warning('请完整填写注册信息')
    return
  }
  if (!registerForm.email.includes('@')) {
    ElMessage.warning('请输入有效邮箱')
    return
  }
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码至少6位')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入密码不一致')
    return
  }

  registering.value = true
  try {
    await authStore.registerStudent(registerForm.email, registerForm.password, registerForm.fullName)
    ElMessage.success('注册成功，请使用学生身份登录')
    form.username = registerForm.email
    form.password = ''
    form.loginMode = 'student'
    registerForm.email = ''
    registerForm.fullName = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    activeTab.value = 'login'
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '注册失败，请稍后重试')
  } finally {
    registering.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
}

.card-header {
  text-align: center;
}

.w-100 {
  width: 100%;
}
</style>
