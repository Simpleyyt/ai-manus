<template>
  <div class="tools-page">
    <div class="tools-header">
      <h1>🛠️ Manus Tools Explorer</h1>
      <p class="subtitle">Comprehensive documentation and introspection for all available tools</p>
      
      <div class="search-bar">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search tools by name, purpose, or functionality..."
          @input="handleSearch"
          class="search-input"
        />
      </div>
    </div>

    <div class="tools-content">
      <div class="sidebar">
        <h3>Categories</h3>
        <ul class="category-list">
          <li
            v-for="category in categories"
            :key="category"
            :class="{ active: selectedCategory === category }"
            @click="selectCategory(category)"
          >
            {{ category }}
          </li>
        </ul>
      </div>

      <div class="main-content">
        <div v-if="loading" class="loading">Loading tools...</div>
        
        <div v-else-if="searchResults.length > 0" class="search-results">
          <h2>Search Results ({{ searchResults.length }})</h2>
          <div v-for="tool in searchResults" :key="tool.name" class="tool-card">
            <h3 @click="selectTool(tool)" class="tool-name">{{ tool.name }}</h3>
            <p class="tool-purpose">{{ tool.purpose }}</p>
          </div>
        </div>

        <div v-else-if="selectedTool" class="tool-detail">
          <div class="tool-detail-header">
            <h2>{{ selectedTool.name }}</h2>
            <span class="category-badge">{{ selectedTool.category }}</span>
          </div>

          <div class="tool-section">
            <h3>Purpose</h3>
            <p>{{ selectedTool.purpose }}</p>
          </div>

          <div class="tool-section">
            <h3>Instructions & Best Practices</h3>
            <ul class="instructions-list">
              <li v-for="(instruction, index) in selectedTool.instructions" :key="index">
                {{ instruction }}
              </li>
            </ul>
          </div>

          <div class="tool-section">
            <h3>Parameters</h3>
            <div class="parameters-table">
              <table>
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th>Type</th>
                    <th>Required</th>
                    <th>Description</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="param in selectedTool.parameters" :key="param.name">
                    <td><code>{{ param.name }}</code></td>
                    <td><span class="type-badge">{{ param.type }}</span></td>
                    <td>
                      <span :class="param.required ? 'required-yes' : 'required-no'">
                        {{ param.required ? 'Yes' : 'No' }}
                      </span>
                    </td>
                    <td>{{ param.description }}</td>
                    <td>
                      <span v-if="param.actions" class="actions-list">
                        {{ param.actions.join(', ') }}
                      </span>
                      <span v-else>All</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="selectedTool.examples && selectedTool.examples.length > 0" class="tool-section">
            <h3>Examples</h3>
            <div v-for="(example, index) in selectedTool.examples" :key="index" class="example-code">
              <code>{{ example }}</code>
            </div>
          </div>
        </div>

        <div v-else class="tool-list">
          <h2>{{ selectedCategory || 'All Tools' }}</h2>
          <div v-for="tool in filteredTools" :key="tool.name" class="tool-card" @click="selectTool(tool)">
            <h3 class="tool-name">{{ tool.name }}</h3>
            <p class="tool-purpose">{{ tool.purpose }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

interface ToolParameter {
  name: string
  type: string
  required: boolean
  description: string
  actions?: string[]
  nested_properties?: ToolParameter[]
}

interface Tool {
  name: string
  category: string
  purpose: string
  instructions: string[]
  parameters: ToolParameter[]
  examples?: string[]
}

interface ToolCategory {
  name: string
  description: string
  tools: Tool[]
}

const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedTool = ref<Tool | null>(null)
const categories = ref<string[]>([])
const allTools = ref<ToolCategory[]>([])
const searchResults = ref<Tool[]>([])
const loading = ref(true)

const filteredTools = computed(() => {
  if (!selectedCategory.value) {
    return allTools.value.flatMap(cat => cat.tools)
  }
  const category = allTools.value.find(cat => cat.name === selectedCategory.value)
  return category ? category.tools : []
})

const selectCategory = (category: string) => {
  selectedCategory.value = category
  selectedTool.value = null
  searchQuery.value = ''
  searchResults.value = []
}

const selectTool = (tool: Tool) => {
  selectedTool.value = tool
  searchResults.value = []
}

const handleSearch = async () => {
  if (searchQuery.value.trim().length < 2) {
    searchResults.value = []
    return
  }

  try {
    const response = await axios.get(`/api/tools/search?q=${encodeURIComponent(searchQuery.value)}`)
    searchResults.value = response.data
  } catch (error) {
    console.error('Search error:', error)
  }
}

onMounted(async () => {
  try {
    // Fetch all tools
    const toolsResponse = await axios.get('/api/tools/')
    allTools.value = toolsResponse.data

    // Fetch categories
    const categoriesResponse = await axios.get('/api/tools/categories')
    categories.value = categoriesResponse.data

    loading.value = false
  } catch (error) {
    console.error('Error loading tools:', error)
    loading.value = false
  }
})
</script>

<style scoped>
.tools-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.tools-header {
  text-align: center;
  color: white;
  margin-bottom: 2rem;
}

.tools-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin-bottom: 1.5rem;
}

.search-bar {
  max-width: 600px;
  margin: 0 auto;
}

.search-input {
  width: 100%;
  padding: 1rem;
  font-size: 1rem;
  border: none;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tools-content {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.sidebar {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  height: fit-content;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.sidebar h3 {
  margin-bottom: 1rem;
  color: #667eea;
}

.category-list {
  list-style: none;
  padding: 0;
}

.category-list li {
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.category-list li:hover {
  background: #f3f4f6;
}

.category-list li.active {
  background: #667eea;
  color: white;
}

.main-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  min-height: 500px;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #667eea;
  font-size: 1.2rem;
}

.tool-list, .search-results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.tool-list h2, .search-results h2 {
  grid-column: 1 / -1;
  color: #667eea;
  margin-bottom: 1rem;
}

.tool-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

.tool-name {
  color: #667eea;
  margin-bottom: 0.5rem;
  font-family: 'Courier New', monospace;
}

.tool-purpose {
  color: #6b7280;
  font-size: 0.95rem;
}

.tool-detail {
  max-width: 1000px;
}

.tool-detail-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.tool-detail-header h2 {
  color: #667eea;
  font-family: 'Courier New', monospace;
}

.category-badge {
  background: #667eea;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.tool-section {
  margin-bottom: 2rem;
}

.tool-section h3 {
  color: #374151;
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.instructions-list {
  list-style: none;
  padding: 0;
}

.instructions-list li {
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background: #f9fafb;
  border-left: 4px solid #667eea;
  border-radius: 4px;
}

.parameters-table {
  overflow-x: auto;
}

.parameters-table table {
  width: 100%;
  border-collapse: collapse;
}

.parameters-table th {
  background: #f3f4f6;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
}

.parameters-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.parameters-table code {
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  color: #667eea;
}

.type-badge {
  background: #dbeafe;
  color: #1e40af;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.required-yes {
  color: #dc2626;
  font-weight: 600;
}

.required-no {
  color: #6b7280;
}

.actions-list {
  font-size: 0.85rem;
  color: #6b7280;
}

.example-code {
  background: #1f2937;
  color: #10b981;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .tools-content {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }
}
</style>
