<template>
  <div class="result-container">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <span class="text-large font-600 mr-3"> 提交结果 </span>
        </template>
      </el-page-header>
      <el-button type="danger" @click="handleLogout">退出登录</el-button>
    </div>

    <el-card v-loading="loading" class="box-card">
      <template #header>
        <div class="card-header">
          <span>提交 ID: {{ submissionId }}</span>
          <el-tag :type="getStatusType(submission?.status)">{{ submission?.status || 'Loading...' }}</el-tag>
        </div>
      </template>

      <div v-if="submission">
        <div class="section score-section" v-if="finalScore !== null">
          <h3>最终评分</h3>
          <el-progress :percentage="Number(finalScore)" :status="getScoreStatus(Number(finalScore))" />
          <p class="score-line">总分: {{ finalScore }} / 100</p>
        </div>

        <el-descriptions title="执行结果" :column="1" border>
          <el-descriptions-item label="语言">{{ submission.language }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ new Date(submission.created_at).toLocaleString() }}</el-descriptions-item>
        </el-descriptions>

        <div class="section">
          <h3>代码内容</h3>
          <pre class="code-block">{{ submission.code_content }}</pre>
        </div>

        <div v-if="executionResult" class="section">
          <h3>运行输出</h3>
          <el-alert
            v-if="executionResult.exit_code === 0"
            title="执行成功"
            type="success"
            :closable="false"
            show-icon
          />
          <el-alert
            v-else
            title="执行失败"
            type="error"
            :closable="false"
            show-icon
          />
          
          <div class="output-console">
            <div v-if="executionResult.stdout">
              <strong>STDOUT:</strong>
              <pre>{{ executionResult.stdout }}</pre>
            </div>
            <div v-if="executionResult.stderr" class="error-text">
              <strong>STDERR:</strong>
              <pre>{{ executionResult.stderr }}</pre>
            </div>
          </div>
        </div>

        <div v-if="analysisResult" class="section">
          <h3>静态分析</h3>
          <el-alert
            v-if="blankSubmissionDetected"
            :title="blankSubmissionReason"
            type="warning"
            :closable="false"
            show-icon
          />
          <p v-if="blankSubmissionDetected" class="blank-meta">
            有效非模板代码行数: {{ blankSubmissionLineCount }}
          </p>
          <el-progress :percentage="analysisResult.score || 0" :status="getScoreStatus(analysisResult.score || 0)" />
          <p>评分: {{ analysisResult.score }} / 100</p>
          
          <div v-if="analysisResult.issues">
             <h4>发现的问题:</h4>
             <pre>{{ JSON.stringify(analysisResult.issues, null, 2) }}</pre>
          </div>
        </div>
        
        <div class="section" v-if="feedbackText">
            <h3>AI 反馈</h3>
          <div class="feedback-content">{{ feedbackText }}</div>

          <div v-if="gradeBreakdown" class="breakdown-block">
            <h4>评分细则</h4>
            <pre>{{ JSON.stringify(gradeBreakdown, null, 2) }}</pre>
          </div>
        </div>

        <div class="section" v-else>
          <h3>AI 反馈</h3>
          <el-empty description="AI 反馈生成中，请稍后刷新" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '../utils/request'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const submissionId = route.params.id
const loading = ref(true)
const submission = ref<any>(null)
const executionResult = ref<any>(null)
const analysisResult = ref<any>(null)
const feedbackText = ref('')
const finalScore = ref<number | null>(null)
const gradeBreakdown = ref<any>(null)
let pollInterval: any = null

const blankSubmissionDetected = computed(() => {
  return Boolean(analysisResult.value?.issues?.blank_submission_detected)
})

const blankSubmissionReason = computed(() => {
  return analysisResult.value?.issues?.blank_submission_reason || '检测到白卷/模板提交'
})

const blankSubmissionLineCount = computed(() => {
  const count = analysisResult.value?.issues?.student_non_template_line_count
  return typeof count === 'number' ? count : 0
})

const goBack = () => {
  router.push('/')
}

const handleLogout = () => {
  authStore.logout()
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'pending': return 'warning'
    default: return 'info'
  }
}

const getScoreStatus = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 60) return 'warning'
  return 'exception'
}

const fetchResult = async () => {
  try {
    const response = await request.get(`/submissions/${submissionId}`)
    submission.value = response.data
    
  executionResult.value = submission.value.execution_result || null
  analysisResult.value = submission.value.static_analysis || null
  feedbackText.value = submission.value.feedback?.content || ''
  finalScore.value = submission.value.feedback?.final_score ?? null
  gradeBreakdown.value = submission.value.feedback?.grade_breakdown ?? null

    loading.value = false
    
  if (submission.value.status && submission.value.status !== 'pending') {
        clearInterval(pollInterval)
    }
    
  } catch (error) {
    console.error(error)
    loading.value = false
    clearInterval(pollInterval)
  }
}

onMounted(() => {
  fetchResult()
  pollInterval = setInterval(fetchResult, 2000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.result-container {
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

.section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.code-block {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
}

.output-console {
  background-color: #1e1e1e;
  color: #fff;
  padding: 15px;
  border-radius: 4px;
  margin-top: 10px;
  font-family: monospace;
}

.error-text {
  color: #f56c6c;
}

.feedback-content {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  white-space: pre-wrap;
  line-height: 1.7;
}

.score-section {
  border-top: none;
  padding-top: 0;
}

.score-line {
  margin-top: 8px;
  font-weight: 600;
}

.blank-meta {
  margin: 8px 0 10px;
  color: #e6a23c;
  font-size: 13px;
}

.breakdown-block {
  margin-top: 12px;
}
</style>
