<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">管理</p>
      <h1 class="page-title">管理后台</h1>
      <p class="page-desc">审核、发布、下线竞赛，查看报名并导出 CSV。</p>
    </div>

    <div class="btn-group">
      <button class="btn btn-primary" @click="handleIngest" v-if="isAdmin">导入数据源</button>
      <router-link class="btn btn-secondary" to="/admin/api-config" v-if="isAdmin">系统配置</router-link>
    </div>

    <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>

    <div class="card">
      <h2 class="section-title">待审核竞赛</h2>
      <ul class="grid" v-if="pending.length">
        <li v-for="item in pending" :key="item.id" class="card">
          <div class="card-row">
            <div>
              <div class="card-title">{{ item.title }}</div>
              <p class="card-meta">来源：{{ item.source }}</p>
              <p class="card-meta">认可：{{ item.level === "school" ? "学校认可" : "国家认可" }}</p>
              <p class="card-meta">学校：{{ item.school || "ALL" }}</p>
              <p class="card-meta" v-if="item.contact_note">备注：{{ item.contact_note }}</p>
            </div>
            <div class="btn-group">
              <button v-if="canReview" class="btn btn-primary btn-sm" @click="publish(item.id)">发布</button>
              <button class="btn btn-secondary btn-sm" @click="startEdit(item)">编辑</button>
              <span v-if="!canReview" class="card-meta">仅学校管理员可审核</span>
            </div>
          </div>
        </li>
      </ul>
      <p v-else class="empty">暂无待审核竞赛</p>
    </div>

    <div class="card">
      <h2 class="section-title">已发布竞赛</h2>
      <ul class="grid" v-if="published.length">
        <li v-for="item in published" :key="item.id" class="card">
          <div class="card-row">
            <div>
              <div class="card-title">{{ item.title }}</div>
              <p class="card-meta">学校：{{ item.school || "ALL" }} ｜ 来源：{{ item.source }}</p>
            </div>
            <div class="btn-group">
              <button class="btn btn-secondary btn-sm" @click="handleViewRegistrations(item.id)">查看报名</button>
              <button class="btn btn-secondary btn-sm" @click="handleExportRegistrations(item.id)">导出 CSV</button>
              <button class="btn btn-secondary btn-sm" @click="startEdit(item)">编辑</button>
              <button v-if="canReview" class="btn btn-secondary btn-sm" @click="unpublish(item.id)">下线</button>
            </div>
          </div>

          <ul v-if="registrations[item.id]?.length" class="grid" style="margin-top: 12px">
            <li v-for="row in registrations[item.id]" :key="row.id" class="card card-row">
              <div>
                <div class="card-title">{{ row.username }}</div>
                <p class="card-meta">{{ row.email }}</p>
              </div>
              <span class="tag">{{ row.status }}</span>
            </li>
          </ul>
          <p v-else-if="registrationLoaded[item.id]" class="card-meta" style="margin-top: 12px">暂无报名记录</p>
        </li>
      </ul>
      <p v-else class="empty">暂无已发布竞赛</p>
    </div>

    <div class="card" v-if="editingId">
      <h2 class="section-title">编辑竞赛 #{{ editingId }}</h2>
      <form class="form form-wide" @submit.prevent="handleSaveEdit">
        <label class="field">
          <span class="field-label">标题</span>
          <input v-model="editForm.title" class="input" />
        </label>
        <label class="field">
          <span class="field-label">认可类型</span>
          <select v-model="editForm.level" class="input">
            <option value="school">学校认可</option>
            <option value="national">国家认可</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">学校</span>
          <input v-model="editForm.school" class="input" :disabled="!isAdmin" />
        </label>
        <label class="field">
          <span class="field-label">主办方</span>
          <input v-model="editForm.organizer" class="input" />
        </label>
        <label class="field">
          <span class="field-label">比赛备注</span>
          <input v-model="editForm.contact_note" class="input" />
        </label>
        <label class="field">
          <span class="field-label">标签（逗号分隔）</span>
          <input v-model="editForm.tags" class="input" />
        </label>
        <div class="btn-group">
          <button class="btn btn-primary" type="submit">保存修改</button>
          <button class="btn btn-secondary" type="button" @click="cancelEdit">取消</button>
        </div>
      </form>
    </div>

    <div class="card" v-if="isAdmin">
      <h2 class="section-title">数据源健康</h2>
      <ul class="grid" v-if="sourceMetrics.length">
        <li v-for="source in sourceMetrics" :key="source.source_id" class="card card-row">
          <div>
            <div class="card-title">{{ source.source_id }}</div>
            <p class="card-meta">类型：{{ source.source_type }} ｜ 优先级：{{ source.priority }}</p>
            <p class="card-meta">成功率：{{ (source.success_rate * 100).toFixed(1) }}% ｜ 解析异常：{{ source.parse_error_count }}</p>
          </div>
          <span class="tag">{{ source.health_status }}</span>
        </li>
      </ul>
      <p v-else class="empty">暂无数据源指标</p>
    </div>

    <div class="card">
      <h2 class="section-title">手动录入</h2>
      <form @submit.prevent="handleCreate" class="form form-wide">
        <p class="card-meta">当前角色：{{ roleLabel }}；当前学校：{{ school || "未设置" }}</p>
        <label class="field">
          <span class="field-label">竞赛标题</span>
          <input v-model="form.title" class="input" required />
        </label>
        <label class="field">
          <span class="field-label">认可类型</span>
          <select v-model="form.level" class="input">
            <option value="school">学校认可</option>
            <option value="national">国家认可</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">所属学校</span>
          <input
            v-model="form.school"
            class="input"
            :disabled="!isAdmin"
            placeholder="示例：清华大学（学校管理员默认使用自己学校）"
          />
        </label>
        <label class="field">
          <span class="field-label">主办方</span>
          <input v-model="form.organizer" class="input" placeholder="示例：计算机学院团委" />
        </label>
        <label class="field">
          <span class="field-label">比赛备注（用于群号等）</span>
          <input v-model="form.contact_note" class="input" placeholder="示例：答疑QQ群 123456789；仅限本校同学" />
        </label>
        <label class="field">
          <span class="field-label">标签（逗号分隔）</span>
          <input v-model="form.tags" class="input" placeholder="示例：程序设计, 校级, 创新创业" />
        </label>
        <button class="btn btn-primary" type="submit">提交</button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import { useAuth } from "../../../core/auth-store";
import { useAdminApi } from "../api";

const {
  createCompetition,
  fetchCompetitions,
  ingestSource,
  updateCompetition,
  publishCompetition,
  unpublishCompetition,
  fetchCompetitionRegistrations,
  downloadCompetitionRegistrationsCsv,
  fetchIngestionSources,
} = useAdminApi();

const { isAdmin, role, school } = useAuth();

const roleLabel = computed(() => {
  if (isAdmin.value) return "平台管理员";
  if (role.value === "school_admin") return "学校管理员";
  if (role.value === "student_admin") return "学生管理员";
  return "普通用户";
});

const canReview = computed(() => isAdmin.value || role.value === "school_admin");
const pending = ref([]);
const published = ref([]);
const sourceMetrics = ref([]);
const registrations = reactive({});
const registrationLoaded = reactive({});
const message = ref("");
const msgClass = ref("msg-success");
const editingId = ref(0);

const form = reactive({
  title: "",
  level: "school",
  school: "",
  organizer: "",
  contact_note: "",
  tags: "",
});
const editForm = reactive({
  title: "",
  level: "school",
  school: "",
  organizer: "",
  contact_note: "",
  tags: "",
});

function ok(text) {
  message.value = text;
  msgClass.value = "msg-success";
}

function fail(err, fallback) {
  message.value = err instanceof Error ? err.message : fallback;
  msgClass.value = "msg-error";
}

async function load() {
  pending.value = await fetchCompetitions("pending");
  published.value = await fetchCompetitions("published");
  if (isAdmin.value) {
    const data = await fetchIngestionSources();
    sourceMetrics.value = data.items || [];
  }
}

async function publish(id) {
  message.value = "";
  try {
    await publishCompetition(id);
    ok("竞赛已发布");
    await load();
  } catch (err) {
    fail(err, "发布失败");
  }
}

async function unpublish(id) {
  message.value = "";
  try {
    await unpublishCompetition(id);
    ok("竞赛已下线");
    await load();
  } catch (err) {
    fail(err, "下线失败");
  }
}

async function handleIngest() {
  message.value = "";
  try {
    const data = await ingestSource();
    ok(`导入完成：处理 ${data.processed}，新增 ${data.created}，更新 ${data.updated}`);
    await load();
  } catch (err) {
    fail(err, "导入失败");
  }
}

async function handleCreate() {
  message.value = "";
  try {
    await createCompetition({
      title: form.title,
      level: form.level,
      school: form.school || undefined,
      organizer: form.organizer || undefined,
      contact_note: form.contact_note || undefined,
      tags: form.tags ? form.tags.split(",").map((s) => s.trim()).filter(Boolean) : [],
    });
    form.title = "";
    form.level = "school";
    form.school = "";
    form.organizer = "";
    form.contact_note = "";
    form.tags = "";
    ok("已提交，等待审核");
    await load();
  } catch (err) {
    fail(err, "提交失败");
  }
}

function startEdit(item) {
  editingId.value = item.id;
  editForm.title = item.title || "";
  editForm.level = item.level || "school";
  editForm.school = item.school || "";
  editForm.organizer = item.organizer || "";
  editForm.contact_note = item.contact_note || "";
  editForm.tags = (item.tags || []).join(", ");
}

function cancelEdit() {
  editingId.value = 0;
}

async function handleSaveEdit() {
  message.value = "";
  if (!editingId.value) return;

  try {
    await updateCompetition(editingId.value, {
      title: editForm.title.trim() || undefined,
      level: editForm.level || undefined,
      school: editForm.school.trim() || undefined,
      organizer: editForm.organizer.trim() || undefined,
      contact_note: editForm.contact_note.trim() || undefined,
      tags: editForm.tags
        ? editForm.tags.split(",").map((s) => s.trim()).filter(Boolean)
        : undefined,
    });
    ok("竞赛信息已更新");
    editingId.value = 0;
    await load();
  } catch (err) {
    fail(err, "更新竞赛失败");
  }
}

async function handleViewRegistrations(competitionId) {
  message.value = "";
  try {
    registrations[competitionId] = await fetchCompetitionRegistrations(competitionId);
    registrationLoaded[competitionId] = true;
  } catch (err) {
    fail(err, "加载报名列表失败");
  }
}

async function handleExportRegistrations(competitionId) {
  message.value = "";
  try {
    const blob = await downloadCompetitionRegistrationsCsv(competitionId);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `competition-${competitionId}-registrations.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    ok("报名 CSV 已开始下载");
  } catch (err) {
    fail(err, "导出报名 CSV 失败");
  }
}

onMounted(async () => {
  if (!isAdmin.value && school.value) {
    form.school = school.value;
  }

  try {
    await load();
  } catch (err) {
    fail(err, "加载管理数据失败");
  }
});
</script>
