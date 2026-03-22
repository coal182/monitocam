<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { recordingsApi, camerasApi, type Camera } from '../api/client'

const gifs = ref<any[]>([])
const cameras = ref<Camera[]>([])
const loading = ref(false)
const selectedCamera = ref<number | null>(null)
const selectedGif = ref<any>(null)
const autoRefresh = ref(true)
let refreshInterval: number | null = null



interface GifItem {
  id: string
  camera_id: number
  camera_name: string
  filename: string
  path: string
  timestamp: string
  size: number
}

const loadGifs = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (selectedCamera.value) params.camera_id = selectedCamera.value
    const response = await recordingsApi.listGifs(params)
    gifs.value = response.data
  } catch (e) {
    console.error('Error loading gifs:', e)
  } finally {
    loading.value = false
  }
}

const deleteGif = async (gif: GifItem, event: Event) => {
  event.stopPropagation()
  if (!confirm(`Eliminar grabación ${gif.filename}?`)) return
  try {
    await recordingsApi.delete(gif.id)
    await loadGifs()
  } catch (e) {
    console.error('Error deleting:', e)
  }
}

const loadCameras = async () => {
  try {
    const response = await camerasApi.list()
    cameras.value = response.data
  } catch (e) {
    console.error('Error loading cameras:', e)
  }
}

const formatSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

const formatTimestamp = (ts: string) => {
  if (!ts) return ''
  const parts = ts.split('_')
  if (parts.length >= 2) {
    const date = parts[parts.length - 2]
    const time = parts[parts.length - 1].replace('-', ':')
    return `${date} ${time}`
  }
  return ts.replace(/_/g, ' ')
}


const openVideo = (gif: GifItem) => {
  selectedGif.value = gif
}

const closeVideo = () => {
  selectedGif.value = null
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  if (refreshInterval) return
  refreshInterval = window.setInterval(loadGifs, 10000)
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

onMounted(() => {
  loadCameras()
  loadGifs()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="recordings-page">
    <div class="header">
      <h1>Grabaciones</h1>
      <div class="header-actions">
        <button @click="loadGifs" class="btn-refresh">
          Actualizar
        </button>
        <button @click="toggleAutoRefresh" :class="['btn-auto', { active: autoRefresh }]">
          {{ autoRefresh ? 'Auto ON' : 'Auto OFF' }}
        </button>
      </div>
    </div>

    <div class="filters">
      <div class="filter-group">
        <label>Camara</label>
        <select v-model="selectedCamera" @change="loadGifs">
          <option :value="null">Todas</option>
          <option v-for="cam in cameras" :key="cam.id" :value="cam.id">
            {{ cam.name }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <span class="count">{{ gifs.length }} grabaciones</span>
      </div>
    </div>

    <div v-if="loading && gifs.length === 0" class="loading">
      Cargando...
    </div>

    <div v-if="selectedGif" class="modal" @click.self="closeVideo">
      <div class="modal-content video-modal">
        <div class="modal-header">
          <div class="modal-info">
            <h2>{{ selectedGif.camera_name }}</h2>
            <span class="timestamp">{{ formatTimestamp(selectedGif.timestamp) }}</span>
          </div>
          <button @click="closeVideo" class="close-btn">X</button>
        </div>
        <video 
          :src="`/api/recordings/${selectedGif.id}/download`" 
          controls 
          autoplay
        >
          Tu navegador no soporta video.
        </video>
        <div class="modal-footer">
          <a :href="`/api/recordings/${selectedGif.id}/download`" class="btn-download" download>
            Descargar MP4
          </a>
        </div>
      </div>
    </div>

    <div v-if="!loading && gifs.length === 0" class="empty">
      No hay grabaciones
    </div>

    <div v-else class="gifs-grid">
      <div 
        v-for="gif in gifs" 
        :key="gif.id" 
        class="gif-card"
        @click="openVideo(gif)"
      >
        <div class="gif-preview">
          <img 
            :src="`/api/recordings/gifs/${gif.id}/file`" 
            :alt="gif.filename"
            loading="lazy"
          />
          <div class="gif-overlay">
            <span class="play-icon">▶</span>
          </div>
        </div>
        <div class="gif-info">
          <h3>{{ gif.camera_name }}</h3>
          <p class="timestamp">{{ formatTimestamp(gif.timestamp) }}</p>
          <div class="gif-footer">
            <p class="size">{{ formatSize(gif.size) }}</p>
            <button class="btn-delete" @click="deleteGif(gif, $event)" title="Eliminar">
              X
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recordings-page {
  padding: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

h1 {
  color: #1a1a2e;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-refresh {
  background: #4caf50;
}

.btn-refresh:hover {
  background: #45a049;
}

.btn-auto {
  background: #666;
}

.btn-auto.active {
  background: #4caf50;
}

.filters {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group label {
  font-size: 0.75rem;
  color: #666;
}

.filter-group select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 150px;
}

.count {
  color: #888;
  font-size: 0.85rem;
}

button {
  background: #1a1a2e;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

button:hover {
  background: #16213e;
}

.loading, .empty {
  text-align: center;
  color: #666;
  padding: 3rem;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.video-modal {
  background: #1a1a2e;
  border-radius: 8px;
  width: 90%;
  max-width: 900px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #16213e;
}

.modal-info h2 {
  color: white;
  margin: 0;
  font-size: 1rem;
}

.modal-info .timestamp {
  color: #888;
  font-size: 0.85rem;
}

.close-btn {
  background: transparent;
  border: 1px solid white;
  padding: 0.25rem 0.75rem;
}

video {
  width: 100%;
  max-height: 70vh;
  display: block;
  background: #000;
}

.modal-footer {
  padding: 1rem;
  background: #16213e;
}

.btn-download {
  display: inline-block;
  background: #4caf50;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.85rem;
}

.btn-download:hover {
  background: #45a049;
}

.gifs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1rem;
}

.gif-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.gif-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.gif-preview {
  position: relative;
  aspect-ratio: 16/9;
  background: #000;
  overflow: hidden;
}

.gif-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gif-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.gif-card:hover .gif-overlay {
  opacity: 1;
}

.play-icon {
  font-size: 2rem;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.gif-info {
  padding: 0.75rem;
}

.gif-info h3 {
  margin: 0 0 0.25rem 0;
  color: #1a1a2e;
  font-size: 0.9rem;
}

.gif-info .timestamp {
  color: #333;
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.gif-info .size {
  color: #888;
  font-size: 0.75rem;
  margin: 0;
}

.gif-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.btn-delete {
  background: #e94560;
  color: white;
  border: none;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.btn-delete:hover {
  background: #d63650;
}
</style>
