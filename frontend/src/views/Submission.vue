<template>
  <div class="submission-container">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <span class="text-large font-600 mr-3"> 代码提交 </span>
        </template>
      </el-page-header>
      <el-button type="danger" @click="handleLogout">退出登录</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>作业详情</span>
            </div>
          </template>
          <div class="text item">
            <h3>{{ currentAssignment.title }}</h3>
            <p>{{ currentAssignment.description }}</p>
            <p v-if="currentAssignment.exampleInput">示例输入: {{ currentAssignment.exampleInput }}</p>
            <p v-if="currentAssignment.exampleOutput">示例输出: {{ currentAssignment.exampleOutput }}</p>
            <p v-if="loadFailed" class="assignment-hint">
              未能获取作业详情，已加载默认代码模板。
            </p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>代码编辑</span>
              <el-select v-model="language" placeholder="Select" size="small" style="width: 100px">
                <el-option label="C++" value="cpp" />
              </el-select>
            </div>
          </template>
          
          <el-input
            v-model="code"
            :rows="20"
            type="textarea"
            placeholder="在此处编写您的代码..."
            class="code-editor"
          />
          
          <div class="actions">
            <el-button type="primary" @click="submitCode" :loading="submitting">
              提交代码
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

type AssignmentConfig = {
  id: number
  title: string
  description: string
  exampleInput: string
  exampleOutput: string
  starterCode: string
  language: 'cpp'
}

const assignmentCatalog: Record<number, AssignmentConfig> = {
  1: {
    id: 1,
    title: 'C++ 作业：基础加减法',
    description: '输入两个整数 a 和 b，输出 a+b 和 a-b。',
    exampleInput: '10 6',
    exampleOutput: '16 4',
    starterCode:
      '#include <iostream>\nusing namespace std;\n\nint main() {\n    long long a, b;\n    cin >> a >> b;\n\n    // TODO: 输出 a+b 和 a-b\n\n    return 0;\n}\n',
    language: 'cpp',
  },
}

const defaultAssignment = assignmentCatalog[1]!

const assignmentId = computed(() => Number(route.query.assignmentId) || 1)
const assignmentDetail = ref<Partial<AssignmentConfig> | null>(null)
const loadFailed = ref(false)
const currentAssignment = computed<AssignmentConfig>(() => ({
  ...defaultAssignment,
  ...(assignmentDetail.value || {}),
}))

const language = ref('cpp')
const code = ref('')
const submitting = ref(false)

const fetchAssignmentDetail = async () => {
  loadFailed.value = false
  assignmentDetail.value = null
  try {
    const response = await request.get(`/assignments/${assignmentId.value}`)
    assignmentDetail.value = {
      id: response.data.id,
      title: response.data.title || defaultAssignment.title,
      description: response.data.description || '暂无作业描述。',
      exampleInput: '',
      exampleOutput: '',
      starterCode: defaultAssignment.starterCode,
      language: 'cpp',
    }
  } catch (error) {
    loadFailed.value = true
    assignmentDetail.value = assignmentCatalog[assignmentId.value] ?? defaultAssignment
  }
}

watch(
  assignmentId,
  () => {
    fetchAssignmentDetail()
  },
  { immediate: true }
)

watch(
  currentAssignment,
  (assignment) => {
    language.value = assignment.language
    code.value = assignment.starterCode
  },
  { immediate: true }
)

const goBack = () => {
  router.back()
}

const handleLogout = () => {
  authStore.logout()
}

const submitCode = async () => {
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空')
    return
  }

  submitting.value = true
  try {
    const response = await request.post('/submissions/', {
      assignment_id: assignmentId.value,
      code_content: code.value,
      language: language.value,
    })
    
    ElMessage.success('提交成功')
    router.push({ name: 'Result', params: { id: response.data.id } })
  } catch (error) {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.submission-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.code-editor {
  font-family: 'Consolas', 'Monaco', monospace;
}

.actions {
  margin-top: 20px;
  text-align: right;
}

.assignment-hint {
  margin-top: 12px;
  color: #e6a23c;
  font-size: 13px;
}
</style>
