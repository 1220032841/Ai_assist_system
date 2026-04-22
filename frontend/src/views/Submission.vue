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
              <el-select v-model="language" placeholder="Select" size="small" style="width: 120px" disabled>
                <el-option label="C++" value="cpp" />
                <el-option label="Python" value="python" />
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

type AssignmentLanguage = 'cpp' | 'python'

type AssignmentConfig = {
  id: number
  title: string
  description: string
  exampleInput: string
  exampleOutput: string
  starterCode: string
  language: AssignmentLanguage
}

const defaultAssignmentTemplates: Record<AssignmentLanguage, Omit<AssignmentConfig, 'id'>> = {
  cpp: {
    title: 'C++ 作业',
    description: '请输入题目要求并完成代码实现。',
    exampleInput: '',
    exampleOutput: '',
    starterCode:
      '#include <iostream>\nusing namespace std;\n\nint main() {\n    // TODO: 在这里实现你的逻辑\n    cout << "hello world" << endl;\n    return 0;\n}\n',
    language: 'cpp',
  },
  python: {
    title: 'Python 作业',
    description: '请输入题目要求并完成代码实现。',
    exampleInput: '',
    exampleOutput: '',
    starterCode:
      'def solve():\n    # TODO: 在这里实现你的逻辑\n    pass\n\nif __name__ == "__main__":\n    solve()\n',
    language: 'python',
  },
}

const normalizeAssignmentLanguage = (language?: string): AssignmentLanguage =>
  language === 'python' ? 'python' : 'cpp'

const buildDefaultAssignment = (id: number, language: AssignmentLanguage = 'cpp'): AssignmentConfig => ({
  id,
  ...defaultAssignmentTemplates[language],
})

const assignmentId = computed(() => Number(route.query.assignmentId) || 1)
const assignmentDetail = ref<Partial<AssignmentConfig> | null>(null)
const loadFailed = ref(false)
const currentAssignment = computed<AssignmentConfig>(() => ({
  ...buildDefaultAssignment(assignmentId.value, normalizeAssignmentLanguage(assignmentDetail.value?.language)),
  ...(assignmentDetail.value || {}),
}))

const language = ref<AssignmentLanguage>('cpp')
const code = ref('')
const submitting = ref(false)

const fetchAssignmentDetail = async () => {
  loadFailed.value = false
  assignmentDetail.value = null
  try {
    const response = await request.get(`/assignments/${assignmentId.value}`)
    const assignmentLanguage = normalizeAssignmentLanguage(response.data.language)
    const defaults = buildDefaultAssignment(response.data.id, assignmentLanguage)
    assignmentDetail.value = {
      id: response.data.id,
      title: response.data.title || defaults.title,
      description: response.data.description || '暂无作业描述。',
      exampleInput: response.data.example_input || '',
      exampleOutput: response.data.example_output || '',
      starterCode: response.data.starter_code || defaults.starterCode,
      language: assignmentLanguage,
    }
  } catch (error) {
    loadFailed.value = true
    assignmentDetail.value = buildDefaultAssignment(assignmentId.value, 'cpp')
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
