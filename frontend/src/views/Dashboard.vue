<template>
  <div class="dashboard-container">
    <div class="header">
      <h2>我的作业</h2>
      <div class="header-actions">
        <el-button @click="openProfileDialog">个人资料</el-button>
        <el-button type="danger" @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <el-card class="box-card">
      <el-table :data="assignments" style="width: 100%">
        <el-table-column prop="title" label="作业标题" width="180" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="截止日期" width="220">
          <template #default="scope">
            {{ scope.row.due_date ? new Date(scope.row.due_date).toLocaleString() : '未设置' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button
              link
              type="primary"
              size="small"
              @click="goToSubmission(scope.row.id)"
            >
              去提交
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="box-card history-card">
      <template #header>
        <div class="card-title-row">
          <span>提交记录</span>
          <div class="history-actions">
            <el-button size="small" @click="fetchSubmissions">刷新</el-button>
            <el-button
              v-if="!batchMode"
              size="small"
              type="warning"
              :disabled="submissions.length === 0"
              @click="startBatchMode"
            >
              批量删除
            </el-button>
            <el-button
              v-if="batchMode"
              size="small"
              @click="cancelBatchMode"
            >
              取消批量
            </el-button>
            <el-button
              v-if="batchMode"
              size="small"
              type="danger"
              :disabled="selectedSubmissionIds.length === 0"
              @click="handleBulkDelete"
            >
              删除选中({{ selectedSubmissionIds.length }})
            </el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="submissions.length === 0"
              @click="handleDeleteAll"
            >
              一键清空
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="submissions"
        style="width: 100%"
        v-loading="loadingSubmissions"
        row-key="id"
        @selection-change="onSelectionChange"
      >
        <el-table-column v-if="batchMode" type="selection" width="50" />
        <el-table-column prop="id" label="提交ID" width="100" />
        <el-table-column prop="assignment_id" label="作业ID" width="100" />
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column prop="language" label="语言" width="100" />
        <el-table-column label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status || 'unknown' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="200">
          <template #default="scope">
            {{ new Date(scope.row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="viewResult(scope.row.id)">
              查看结果
            </el-button>
            <el-button link type="danger" size="small" @click="handleDeleteOne(scope.row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="profileDialogVisible" title="编辑个人资料" width="420px">
      <el-form :model="profileForm" label-width="80px">
        <el-form-item label="邮箱">
          <el-input :model-value="authStore.user?.email || ''" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingProfile" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import request from '../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const loadingSubmissions = ref(false)
const submissions = ref<any[]>([])
const selectedSubmissionIds = ref<number[]>([])
const batchMode = ref(false)
const profileDialogVisible = ref(false)
const savingProfile = ref(false)
const profileForm = ref({
  full_name: '',
})

const assignments = ref<any[]>([])

const goToSubmission = (id: number) => {
  router.push({ name: 'Submission', query: { assignmentId: id } })
}

const viewResult = (id: number) => {
  router.push({ name: 'Result', params: { id } })
}

const onSelectionChange = (rows: any[]) => {
  selectedSubmissionIds.value = rows.map((row) => row.id)
}

const startBatchMode = () => {
  batchMode.value = true
  selectedSubmissionIds.value = []
  ElMessage.info('请勾选要删除的提交记录，再点击“删除选中”')
}

const cancelBatchMode = () => {
  batchMode.value = false
  selectedSubmissionIds.value = []
}

const getStatusType = (status?: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'pending') return 'warning'
  return 'info'
}

const fetchSubmissions = async () => {
  loadingSubmissions.value = true
  try {
    const response = await request.get('/submissions/')
    submissions.value = response.data
    selectedSubmissionIds.value = []
    if (submissions.value.length === 0) {
      batchMode.value = false
    }
  } catch (error) {
    ElMessage.error('获取提交记录失败')
  } finally {
    loadingSubmissions.value = false
  }
}

const fetchAssignments = async () => {
  try {
    const response = await request.get('/assignments/')
    assignments.value = response.data
  } catch (error) {
    ElMessage.error('获取作业列表失败')
  }
}

const handleDeleteOne = async (id: number) => {
  try {
    await ElMessageBox.confirm('确认删除这条提交记录吗？该操作不可恢复。', '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await request.delete(`/submissions/${id}`)
    ElMessage.success('删除成功')
    await fetchSubmissions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBulkDelete = async () => {
  if (selectedSubmissionIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确认批量删除 ${selectedSubmissionIds.value.length} 条提交记录吗？该操作不可恢复。`,
      '提示',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      }
    )
    await request.post('/submissions/bulk-delete', {
      submission_ids: selectedSubmissionIds.value,
    })
    ElMessage.success('批量删除成功')
    batchMode.value = false
    await fetchSubmissions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleDeleteAll = async () => {
  if (submissions.value.length === 0) return
  try {
    await ElMessageBox.confirm('确认一键清空所有提交记录吗？该操作不可恢复。', '高风险操作', {
      type: 'warning',
      confirmButtonText: '清空',
      cancelButtonText: '取消',
    })
    await request.delete('/submissions/')
    ElMessage.success('已清空提交记录')
    batchMode.value = false
    await fetchSubmissions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

const handleLogout = () => {
  authStore.logout()
}

const openProfileDialog = () => {
  profileForm.value.full_name = authStore.user?.full_name || ''
  profileDialogVisible.value = true
}

const saveProfile = async () => {
  savingProfile.value = true
  try {
    await request.patch('/users/me', {
      full_name: profileForm.value.full_name,
    })
    await authStore.fetchUser()
    ElMessage.success('个人资料更新成功')
    profileDialogVisible.value = false
  } catch (error) {
    ElMessage.error('更新个人资料失败')
  } finally {
    savingProfile.value = false
  }
}

onMounted(() => {
  fetchAssignments()
  fetchSubmissions()
})
</script>

<style scoped>
.dashboard-container {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.history-card {
  margin-top: 20px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history-actions {
  display: flex;
  gap: 8px;
}
</style>
