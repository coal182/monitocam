<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { camerasApi, type Camera } from '../api/client'

const cameras = ref<Camera[]>([])
const loading = ref(false)
const showAddForm = ref(false)
const newCamera = ref({ name: '', rtsp_url: '', enabled: true })
const error = ref('')

const loadCameras = async () => {
  loading.value = true
  try {
    const response = await camerasApi.list()
    cameras.value = response.data
  } catch (e) {
    error.value = 'Error loading cameras'
  } finally {
    loading.value = false
  }
}

const addCamera = async () => {
  try {
    await camerasApi.create(newCamera.value)
    showAddForm.value = false
    newCamera.value = { name: '', rtsp_url: '', enabled: true }
    await loadCameras()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Error adding camera'
  }
}

const deleteCamera = async (id: number) => {
  if (confirm('Delete this camera?')) {
    try {
      await camerasApi.delete(id)
      await loadCameras()
    } catch (e) {
      error.value = 'Error deleting camera'
    }
  }
}

const toggleRecording = async (camera: Camera) => {
  try {
    if (camera.status === 'recording') {
      await camerasApi.stopRecording(camera.id)
    } else {
      await camerasApi.startRecording(camera.id)
    }
    await loadCameras()
  } catch (e) {
    error.value = 'Error toggling recording'
  }
}

onMounted(loadCameras)
</script>

<template>
  <div class="cameras-page">
    <div class="header">
      <h1>Camaras</h1>
      <button @click="showAddForm = true">+ Anadir Camara</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="showAddForm" class="modal">
      <div class="modal-content">
        <h2>Nueva Camara</h2>
        <form @submit.prevent="addCamera">
          <div class="form-group">
            <label>Nombre</label>
            <input v-model="newCamera.name" required />
          </div>
          <div class="form-group">
            <label>URL RTSP</label>
            <input v-model="newCamera.rtsp_url" required placeholder="rtsp://..." />
          </div>
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="newCamera.enabled" />
              Habilitada
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddForm = false">Cancelar</button>
            <button type="submit">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="loading" class="loading">Cargando...</div>

    <div v-else class="cameras-grid">
      <div v-for="camera in cameras" :key="camera.id" class="camera-card">
        <div class="camera-header">
          <h3>{{ camera.name }}</h3>
          <span :class="['status', camera.status]">{{ camera.status }}</span>
        </div>
        <div class="camera-info">
          <p><strong>URL:</strong> {{ camera.rtsp_url }}</p>
          <p><strong>ID:</strong> {{ camera.id }}</p>
        </div>
        <div class="camera-actions">
          <button @click="toggleRecording(camera)">
            {{ camera.status === 'recording' ? 'Parar' : 'Grabar' }}
          </button>
          <button @click="deleteCamera(camera.id)" class="danger">Eliminar</button>
        </div>
      </div>
    </div>

    <div v-if="!loading && cameras.length === 0" class="empty">
      No hay camaras configuradas
    </div>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

h1 {
  color: #1a1a2e;
}

button {
  background: #1a1a2e;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #16213e;
}

button.danger {
  background: #e94560;
}

button.danger:hover {
  background: #d63650;
}

.error {
  background: #fee;
  color: #c33;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 100%;
  max-width: 500px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.form-group.checkbox input[type="checkbox"] {
  width: auto;
  padding: 0;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #1a1a2e;
}

.form-group input::placeholder {
  color: #aaa;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.modal-actions button[type="button"] {
  background: #ccc;
}

.cameras-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.camera-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
}

.status.recording {
  background: #4caf50;
  color: white;
}

.status.stopped {
  background: #ff9800;
  color: white;
}

.status.disabled {
  background: #9e9e9e;
  color: white;
}

.camera-info p {
  margin: 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
  word-break: break-all;
}

.camera-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.camera-actions button {
  flex: 1;
  padding: 0.5rem;
  font-size: 0.9rem;
}

.loading, .empty {
  text-align: center;
  color: #666;
  padding: 2rem;
}
</style>
