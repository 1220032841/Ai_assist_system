<template>
  <div class="teacher-container">
    <div class="header">
      <h2>教师工作台</h2>
      <div class="actions">
        <el-button @click="reloadAll">刷新数据</el-button>
        <el-button type="success" :disabled="exportRows.length === 0" @click="exportCsv">
          导出CSV
        </el-button>
        <el-button type="danger" @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <el-card>
      <el-tabs v-model="activeModule">
        <el-tab-pane label="班级模块" name="class">
          <div class="block-toolbar">
            <el-input v-model="newClassName" placeholder="新建班级名称" clearable style="width: 220px" />
            <el-button type="primary" :loading="creatingClass" @click="createClassGroup">创建班级</el-button>
          </div>

          <el-row :gutter="16" class="module-grid">
            <el-col :span="10">
              <div class="module-panel">
                <div class="module-panel-header">班级列表</div>
                <div class="module-panel-toolbar">
                  <el-input v-model="classKeyword" placeholder="查询班级" clearable style="width: 260px" />
                </div>
                <div class="module-panel-table">
                  <el-table :data="filteredClassList" v-loading="loading" height="410" @row-click="onClassRowClick">
                    <el-table-column prop="class_name" label="班级" min-width="150" />
                    <el-table-column prop="student_count" label="人数" width="90" />
                    <el-table-column label="操作" width="170">
                      <template #default="scope">
                        <el-button
                          v-if="scope.row.group_id"
                          link
                          type="primary"
                          @click.stop="openClassEditDialog(scope.row)"
                        >
                          改名
                        </el-button>
                        <el-button
                          v-if="scope.row.group_id"
                          link
                          type="danger"
                          @click.stop="deleteClassGroup(scope.row)"
                        >
                          删除
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-col>
            <el-col :span="14">
              <div class="module-panel">
                <div class="module-panel-header">{{ selectedClassName ? `${selectedClassName} 学生列表` : '请选择班级' }}</div>
                <div class="module-panel-toolbar">
                  <el-input
                    v-model="classStudentKeyword"
                    :disabled="!selectedClassName"
                    placeholder="查询班级内学生"
                    clearable
                    style="width: 280px"
                  />
                  <el-button
                    type="primary"
                    :disabled="!canManageSelectedClass"
                    @click="openAddStudentDialog"
                  >
                    添加学生
                  </el-button>
                </div>
                <div class="module-panel-table">
                  <el-table :data="filteredSelectedClassStudents" height="410">
                    <el-table-column label="学生姓名" min-width="140">
                      <template #default="scope">
                        {{ displayStudentName(scope.row) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="email" label="账号" min-width="180" />
                    <el-table-column label="平均最终分" width="120">
                      <template #default="scope">
                        {{ studentAvgScore(scope.row.id).final }}
                      </template>
                    </el-table-column>
                    <el-table-column label="平均静态分" width="120">
                      <template #default="scope">
                        {{ studentAvgScore(scope.row.id).static }}
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="160">
                      <template #default="scope">
                        <el-button link type="primary" @click="openStudentDetail(scope.row)">查看</el-button>
                        <el-button
                          v-if="canManageSelectedClass"
                          link
                          type="danger"
                          @click="removeStudentFromClass(scope.row)"
                        >
                          移除
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="作业模块" name="assignment">
          <div class="block-toolbar">
            <el-button type="primary" @click="openAssignmentDialog">创建作业</el-button>
          </div>

          <el-row :gutter="16" class="module-grid">
            <el-col :span="10">
              <div class="module-panel">
                <div class="module-panel-header">作业列表</div>
                <div class="module-panel-toolbar">
                  <el-input v-model="assignmentKeyword" placeholder="查询作业" clearable style="width: 260px" />
                </div>
                <div class="module-panel-table">
                  <el-table :data="filteredAssignments" v-loading="loading" height="410" @row-click="onAssignmentRowClick">
                    <el-table-column prop="id" label="作业ID" width="90" />
                    <el-table-column prop="title" label="作业标题" min-width="220" />
                  </el-table>
                </div>
              </div>
            </el-col>
            <el-col :span="14">
              <div class="module-panel">
                <div class="module-panel-header">{{ selectedAssignmentTitle ? `${selectedAssignmentTitle} 成绩列表` : '请选择作业' }}</div>
                <div class="module-panel-toolbar">
                  <el-input
                    v-model="assignmentStudentKeyword"
                    :disabled="!selectedAssignmentId"
                    placeholder="查询学生"
                    clearable
                    style="width: 280px"
                  />
                </div>
                <div class="module-panel-table">
                  <el-table :data="filteredAssignmentRows" height="410">
                    <el-table-column label="学生姓名" min-width="140">
                      <template #default="scope">
                        {{ scope.row.student_name || emailName(scope.row.student_email) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="student_email" label="账号" min-width="170" />
                    <el-table-column prop="class_name" label="班级" width="120" />
                    <el-table-column label="最终成绩" width="110">
                      <template #default="scope">
                        <span v-if="scope.row.final_score !== null">{{ scope.row.final_score }}</span>
                        <el-tag v-else type="info">未提交</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column label="静态分析" width="110">
                      <template #default="scope">
                        <span v-if="scope.row.static_score !== null">{{ scope.row.static_score }}</span>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="status" label="状态" width="120">
                      <template #default="scope">
                        <el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column label="报告" width="120">
                      <template #default="scope">
                        <el-button
                          v-if="scope.row.submission_id"
                          link
                          type="primary"
                          @click="goToSubmissionReport(scope.row.submission_id)"
                        >
                          查看报告
                        </el-button>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="学生模块" name="student">
          <div class="block-toolbar">
            <el-input v-model="studentKeyword" placeholder="查询学生账号或姓名" clearable style="width: 280px" />
          </div>

          <el-table :data="filteredStudents" v-loading="studentsLoading" style="width: 100%">
            <el-table-column label="学生姓名" min-width="150">
              <template #default="scope">
                {{ displayStudentName(scope.row) }}
              </template>
            </el-table-column>
            <el-table-column prop="email" label="账号" min-width="210" />
            <el-table-column label="班级" min-width="170">
              <template #default="scope">
                {{ scope.row.class_name || '未分班' }}
              </template>
            </el-table-column>
            <el-table-column label="平均最终分" width="120">
              <template #default="scope">
                {{ studentAvgScore(scope.row.id).final }}
              </template>
            </el-table-column>
            <el-table-column label="平均静态分" width="120">
              <template #default="scope">
                {{ studentAvgScore(scope.row.id).static }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button size="small" @click="openStudentDetail(scope.row)">查看详情</el-button>
                <el-button size="small" type="danger" @click="deleteStudent(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-drawer v-model="studentDetailVisible" title="学生详情" size="60%">
      <div v-if="studentDetailData?.student" class="detail-card">
        <p><strong>姓名：</strong>{{ studentDetailData.student.full_name || emailName(studentDetailData.student.email) }}</p>
        <p><strong>账号：</strong>{{ studentDetailData.student.email }}</p>
        <p><strong>班级：</strong>{{ studentDetailData.student.class_name || '未分班' }}</p>
      </div>

      <div class="block-toolbar">
        <el-input v-model="studentDetailKeyword" placeholder="查询该学生提交记录（作业名）" clearable style="width: 320px" />
      </div>

      <el-table :data="filteredStudentDetailSubmissions" style="width: 100%" v-loading="studentDetailLoading">
        <el-table-column prop="submission_id" label="提交ID" width="100" />
        <el-table-column prop="assignment_title" label="作业" min-width="220" />
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column label="最终成绩" width="110">
          <template #default="scope">
            <span v-if="scope.row.final_score !== null">{{ scope.row.final_score }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="静态分析" width="110">
          <template #default="scope">
            <span v-if="scope.row.static_score !== null">{{ scope.row.static_score }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="statusType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="180">
          <template #default="scope">
            {{ scope.row.created_at ? new Date(scope.row.created_at).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="AI反馈" width="120">
          <template #default="scope">
            <el-button link type="primary" @click="goToSubmissionReport(scope.row.submission_id)">查看报告</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog v-model="classEditDialogVisible" title="修改班级名称" width="420px">
      <el-form :model="classEditForm" label-width="90px">
        <el-form-item label="原班级名称">
          <el-input :model-value="classEditForm.oldName" disabled />
        </el-form-item>
        <el-form-item label="新班级名称">
          <el-input v-model="classEditForm.newName" placeholder="请输入新班级名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classEditDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="classEditing" @click="submitClassRename">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="addStudentDialogVisible" title="添加学生到班级" width="760px">
      <div class="block-toolbar">
        <el-input
          v-model="addStudentKeyword"
          placeholder="查询学生账号或姓名"
          clearable
          style="width: 280px"
        />
      </div>
      <el-table
        :data="filteredAddableStudents"
        v-loading="studentsLoading"
        row-key="id"
        height="360"
        @selection-change="onAddStudentSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="学生姓名" min-width="150">
          <template #default="scope">
            {{ displayStudentName(scope.row) }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="账号" min-width="200" />
        <el-table-column label="当前班级" min-width="150">
          <template #default="scope">
            {{ scope.row.class_name || '未分班' }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="addStudentDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="addingStudents"
          :disabled="selectedAddStudentIds.length === 0"
          @click="submitAddStudentsToClass"
        >
          添加选中学生（{{ selectedAddStudentIds.length }}）
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assignmentDialogVisible" title="创建作业" width="520px">
      <el-form :model="assignmentForm" label-width="90px">
        <el-form-item label="作业标题">
          <el-input v-model="assignmentForm.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="作业描述">
          <el-input
            v-model="assignmentForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入作业描述"
          />
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="assignmentForm.dueDate"
            type="datetime"
            placeholder="可选"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignmentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingAssignment" @click="submitAssignment">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import request from '../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const router = useRouter()

const loading = ref(false)
const studentsLoading = ref(false)
const activeModule = ref('class')

const gradebook = ref<any[]>([])
const assignments = ref<any[]>([])
const students = ref<any[]>([])
const classGroups = ref<any[]>([])

const classKeyword = ref('')
const classStudentKeyword = ref('')
const selectedClassName = ref('')

const assignmentKeyword = ref('')
const assignmentStudentKeyword = ref('')
const selectedAssignmentId = ref<number | null>(null)
const assignmentDialogVisible = ref(false)
const creatingAssignment = ref(false)
const assignmentForm = ref({
  title: '',
  description: '',
  dueDate: '',
})

const studentKeyword = ref('')

const studentDetailVisible = ref(false)
const studentDetailLoading = ref(false)
const studentDetailData = ref<any>(null)
const studentDetailKeyword = ref('')
const newClassName = ref('')
const creatingClass = ref(false)
const classEditDialogVisible = ref(false)
const classEditing = ref(false)
const classEditForm = ref({
  id: 0,
  oldName: '',
  newName: '',
})
const addStudentDialogVisible = ref(false)
const addStudentKeyword = ref('')
const selectedAddStudentIds = ref<number[]>([])
const addingStudents = ref(false)

const emailName = (email: string) => {
  if (!email) return '未命名'
  return email.split('@')[0]
}

const displayStudentName = (student: any) => student.full_name || emailName(student.email)

const statusType = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'pending') return 'warning'
  if (status === 'not_submitted') return 'info'
  return 'info'
}

const studentScoreMap = computed(() => {
  const map: Record<number, { finalSum: number; finalCnt: number; staticSum: number; staticCnt: number }> = {}
  for (const row of gradebook.value) {
    const key = Number(row.student_id)
    if (!map[key]) {
      map[key] = { finalSum: 0, finalCnt: 0, staticSum: 0, staticCnt: 0 }
    }
    const entry = map[key]
    if (row.final_score !== null && row.final_score !== undefined) {
      entry.finalSum += Number(row.final_score)
      entry.finalCnt += 1
    }
    if (row.static_score !== null && row.static_score !== undefined) {
      entry.staticSum += Number(row.static_score)
      entry.staticCnt += 1
    }
  }
  return map
})

const studentAvgScore = (studentId: number) => {
  const s = studentScoreMap.value[studentId]
  if (!s) return { final: '-', static: '-' }
  const final = s.finalCnt > 0 ? (s.finalSum / s.finalCnt).toFixed(1) : '-'
  const stat = s.staticCnt > 0 ? (s.staticSum / s.staticCnt).toFixed(1) : '-'
  return { final, static: stat }
}

const classList = computed(() => {
  const studentCountMap: Record<string, number> = {}
  for (const s of students.value) {
    if (!s.class_name) continue
    studentCountMap[s.class_name] = (studentCountMap[s.class_name] || 0) + 1
  }

  const rows: Array<{ class_name: string; student_count: number; group_id: number | null }> = classGroups.value.map((g) => ({
    class_name: g.name,
    student_count: studentCountMap[g.name] ?? Number(g.student_count || 0),
    group_id: Number(g.id),
  }))

  const known = new Set(rows.map((r) => r.class_name))
  for (const name of Object.keys(studentCountMap)) {
    if (!known.has(name)) {
      rows.push({ class_name: name, student_count: studentCountMap[name] || 0, group_id: null })
    }
  }

  const unassignedCount = students.value.filter((s) => !s.class_name).length
  rows.push({ class_name: '未分班', student_count: unassignedCount, group_id: null })

  rows.sort((a, b) => a.class_name.localeCompare(b.class_name))
  return rows
})

const filteredClassList = computed(() => {
  const q = classKeyword.value.trim().toLowerCase()
  if (!q) return classList.value
  return classList.value.filter((c) => (c.class_name || '').toLowerCase().includes(q))
})

const selectedClassStudents = computed(() => {
  if (!selectedClassName.value) return []
  return students.value.filter((s) => (s.class_name || '未分班') === selectedClassName.value)
})

const filteredSelectedClassStudents = computed(() => {
  const q = classStudentKeyword.value.trim().toLowerCase()
  if (!q) return selectedClassStudents.value
  return selectedClassStudents.value.filter((s) => {
    const name = displayStudentName(s).toLowerCase()
    return name.includes(q) || (s.email || '').toLowerCase().includes(q)
  })
})

const canManageSelectedClass = computed(() => {
  return !!selectedClassName.value && selectedClassName.value !== '未分班'
})

const addableStudents = computed(() => {
  if (!canManageSelectedClass.value) return []
  const target = selectedClassName.value
  return students.value.filter((s) => (s.class_name || '未分班') !== target)
})

const filteredAddableStudents = computed(() => {
  const q = addStudentKeyword.value.trim().toLowerCase()
  if (!q) return addableStudents.value
  return addableStudents.value.filter((s) => {
    const name = displayStudentName(s).toLowerCase()
    return name.includes(q) || String(s.email || '').toLowerCase().includes(q)
  })
})

const filteredAssignments = computed(() => {
  const q = assignmentKeyword.value.trim().toLowerCase()
  if (!q) return assignments.value
  return assignments.value.filter((a) => String(a.title || '').toLowerCase().includes(q))
})

const selectedAssignmentTitle = computed(() => {
  if (!selectedAssignmentId.value) return ''
  const found = assignments.value.find((a) => a.id === selectedAssignmentId.value)
  return found?.title || `作业 ${selectedAssignmentId.value}`
})

const assignmentRows = computed(() => {
  if (!selectedAssignmentId.value) return []
  return gradebook.value.filter((r) => r.assignment_id === selectedAssignmentId.value)
})

const filteredAssignmentRows = computed(() => {
  const q = assignmentStudentKeyword.value.trim().toLowerCase()
  if (!q) return assignmentRows.value
  return assignmentRows.value.filter((r) => {
    const name = String(r.student_name || emailName(r.student_email)).toLowerCase()
    return name.includes(q) || String(r.student_email || '').toLowerCase().includes(q)
  })
})

const filteredStudents = computed(() => {
  const q = studentKeyword.value.trim().toLowerCase()
  if (!q) return students.value
  return students.value.filter((s) => {
    const name = displayStudentName(s).toLowerCase()
    return name.includes(q) || (s.email || '').toLowerCase().includes(q)
  })
})

const filteredStudentDetailSubmissions = computed(() => {
  const list = studentDetailData.value?.submissions || []
  const q = studentDetailKeyword.value.trim().toLowerCase()
  if (!q) return list
  return list.filter((row: any) => String(row.assignment_title || '').toLowerCase().includes(q))
})

const exportRows = computed(() => {
  if (activeModule.value === 'assignment' && selectedAssignmentId.value) return filteredAssignmentRows.value
  if (activeModule.value === 'student') {
    return filteredStudents.value.map((s) => ({
      student_name: displayStudentName(s),
      student_email: s.email,
      class_name: s.class_name || '未分班',
      avg_final: studentAvgScore(s.id).final,
      avg_static: studentAvgScore(s.id).static,
    }))
  }
  return gradebook.value
})

const fetchGradebook = async () => {
  const response = await request.get('/analytics/gradebook')
  gradebook.value = response.data
}

const fetchAssignments = async () => {
  const response = await request.get('/assignments/')
  assignments.value = response.data
}

const fetchClassGroups = async () => {
  const response = await request.get('/users/class-groups')
  classGroups.value = response.data
}

const fetchStudents = async () => {
  studentsLoading.value = true
  try {
    const response = await request.get('/users/students')
    students.value = response.data
  } finally {
    studentsLoading.value = false
  }
}

const reloadAll = async () => {
  loading.value = true
  try {
    await Promise.all([fetchGradebook(), fetchAssignments(), fetchStudents(), fetchClassGroups()])
    if (selectedAssignmentId.value && !assignments.value.some((a) => a.id === selectedAssignmentId.value)) {
      selectedAssignmentId.value = null
    }
    if (selectedClassName.value && !classList.value.some((c) => c.class_name === selectedClassName.value)) {
      selectedClassName.value = ''
    }
  } catch (error) {
    ElMessage.error('加载教师数据失败')
  } finally {
    loading.value = false
  }
}

const createClassGroup = async () => {
  const name = newClassName.value.trim()
  if (!name) {
    ElMessage.warning('请输入班级名称')
    return
  }

  creatingClass.value = true
  try {
    await request.post('/users/class-groups', { name })
    ElMessage.success('班级创建成功')
    newClassName.value = ''
    await fetchClassGroups()
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '创建班级失败')
  } finally {
    creatingClass.value = false
  }
}

const openAssignmentDialog = () => {
  assignmentForm.value = {
    title: '',
    description: '',
    dueDate: '',
  }
  assignmentDialogVisible.value = true
}

const submitAssignment = async () => {
  const title = assignmentForm.value.title.trim()
  if (!title) {
    ElMessage.warning('请输入作业标题')
    return
  }

  creatingAssignment.value = true
  try {
    await request.post('/assignments/', {
      title,
      description: assignmentForm.value.description.trim() || null,
      due_date: assignmentForm.value.dueDate || null,
    })
    ElMessage.success('作业创建成功')
    assignmentDialogVisible.value = false
    await fetchAssignments()
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '创建作业失败')
  } finally {
    creatingAssignment.value = false
  }
}

const openClassEditDialog = (row: any) => {
  if (!row.group_id) return
  classEditForm.value = {
    id: Number(row.group_id),
    oldName: row.class_name,
    newName: row.class_name,
  }
  classEditDialogVisible.value = true
}

const submitClassRename = async () => {
  const id = Number(classEditForm.value.id)
  const newName = classEditForm.value.newName.trim()
  if (!id) return
  if (!newName) {
    ElMessage.warning('请输入新班级名称')
    return
  }

  classEditing.value = true
  try {
    await request.patch(`/users/class-groups/${id}`, { name: newName })
    ElMessage.success('班级名称更新成功')
    if (selectedClassName.value === classEditForm.value.oldName) {
      selectedClassName.value = newName
    }
    classEditDialogVisible.value = false
    await reloadAll()
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '修改班级失败')
  } finally {
    classEditing.value = false
  }
}

const deleteClassGroup = async (row: any) => {
  if (!row.group_id) return
  try {
    await ElMessageBox.confirm(
      `确认删除班级 ${row.class_name} 吗？该班学生将被设置为未分班。`,
      '提示',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      }
    )

    await request.delete(`/users/class-groups/${row.group_id}`)
    ElMessage.success('班级删除成功')
    if (selectedClassName.value === row.class_name) {
      selectedClassName.value = ''
    }
    await reloadAll()
  } catch (error: any) {
    if (error !== 'cancel') {
      const detail = error?.response?.data?.detail
      ElMessage.error(detail || '删除班级失败')
    }
  }
}

const onClassRowClick = (row: any) => {
  selectedClassName.value = row.class_name
}

const openAddStudentDialog = () => {
  if (!canManageSelectedClass.value) {
    ElMessage.warning('请选择一个可管理的班级')
    return
  }
  selectedAddStudentIds.value = []
  addStudentKeyword.value = ''
  addStudentDialogVisible.value = true
}

const onAddStudentSelectionChange = (rows: any[]) => {
  selectedAddStudentIds.value = rows.map((row) => Number(row.id))
}

const submitAddStudentsToClass = async () => {
  if (!canManageSelectedClass.value || selectedAddStudentIds.value.length === 0) return

  addingStudents.value = true
  try {
    await Promise.all(
      selectedAddStudentIds.value.map((id) =>
        request.patch(`/users/students/${id}/class`, { class_name: selectedClassName.value })
      )
    )
    ElMessage.success('添加学生成功')
    addStudentDialogVisible.value = false
    await reloadAll()
  } catch (error) {
    ElMessage.error('添加学生失败')
  } finally {
    addingStudents.value = false
  }
}

const removeStudentFromClass = async (row: any) => {
  if (!canManageSelectedClass.value) return
  try {
    await ElMessageBox.confirm(
      `确认将 ${displayStudentName(row)} 移出班级 ${selectedClassName.value} 吗？`,
      '提示',
      {
        type: 'warning',
        confirmButtonText: '移除',
        cancelButtonText: '取消',
      }
    )

    await request.patch(`/users/students/${row.id}/class`, { class_name: null })
    ElMessage.success('已移出班级')
    await reloadAll()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('移除学生失败')
    }
  }
}

const onAssignmentRowClick = (row: any) => {
  selectedAssignmentId.value = row.id
}

const goToSubmissionReport = (submissionId: number | null | undefined) => {
  const id = Number(submissionId)
  if (!id) {
    ElMessage.warning('该记录暂无可查看报告')
    return
  }
  router.push(`/result/${id}`)
}

const deleteStudent = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除学生账号 ${row.email} 吗？该学生提交记录将一并删除。`,
      '高风险操作',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      }
    )

    await request.delete(`/users/students/${row.id}`)
    ElMessage.success('学生账号已删除')
    await reloadAll()
    if (studentDetailData.value?.student?.id === row.id) {
      studentDetailVisible.value = false
      studentDetailData.value = null
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除学生失败')
    }
  }
}

const openStudentDetail = async (row: any) => {
  studentDetailVisible.value = true
  studentDetailLoading.value = true
  studentDetailKeyword.value = ''
  try {
    const response = await request.get(`/analytics/student-detail/${row.id}`)
    studentDetailData.value = response.data
  } catch (error) {
    ElMessage.error('获取学生详情失败')
  } finally {
    studentDetailLoading.value = false
  }
}

const exportCsv = () => {
  if (exportRows.value.length === 0) return

  const headers = Object.keys(exportRows.value[0])
  const rows = exportRows.value.map((row: any) => headers.map((h) => row[h] ?? ''))

  const escapeCell = (value: string | number) => {
    const s = String(value)
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`
    }
    return s
  }

  const csv = [headers, ...rows].map((line) => line.map(escapeCell).join(',')).join('\n')
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'teacher-export.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const handleLogout = () => {
  authStore.logout()
}

onMounted(() => {
  reloadAll()
})
</script>

<style scoped>
.teacher-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.actions {
  display: flex;
  gap: 8px;
}

.block-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.sub-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.detail-card {
  margin-bottom: 14px;
  background: #f7f9fc;
  padding: 12px;
  border-radius: 8px;
}

.module-grid {
  align-items: stretch;
}

.module-panel {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  height: 520px;
  display: flex;
  flex-direction: column;
}

.module-panel-header {
  min-height: 32px;
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.module-panel-toolbar {
  min-height: 40px;
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.module-panel-table {
  flex: 1;
  min-height: 0;
}
</style>
