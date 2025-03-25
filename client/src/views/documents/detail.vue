<script setup>
import { useRoute } from 'vue-router';
import { ref, onMounted } from 'vue';
import PDFViewerWithNavigation from '@/components/PDFViewerWithNavigation.vue';
import JSONEditor from '@/components/jsoneditor/index.vue';
import axios from 'axios'

const documentDetail = ref(null)

const props = defineProps({
  id: {
    type: String,
    required: true
  }
})

const fetchDocumentDetail = async () => {
  try {
    const response = await axios.get(import.meta.env.VITE_BACKEND_URL + `/documents/${props.id}`);
    const { data, status, message } = response.data;
    documentDetail.value = data;
    console.log(documentDetail.value)
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  fetchDocumentDetail()
});
</script>

<template>
  <div class="space-y-2 mb-4">
    <h1 class="text-xl font-semibold">Document Detail</h1>
    <nav>
      <ol class="list-reset flex items-center">
        <li>
          <router-link to="/docs" class="text-teal-500 hover:underline">Documents</router-link>
        </li>
        <font-awesome-icon class="mx-2" :icon="['fas', 'chevron-right']" size="xs" />
        <li v-if="documentDetail" class="text-gray-500">{{ documentDetail.file_name }}</li>
      </ol>
    </nav>
  </div>
  <div class="flex h-[92%] w-full">
    <JSONEditor
      v-if="documentDetail && documentDetail.data"
      class="h-full overflow-auto w-1/2" :sections="documentDetail.data"
    />
    <PDFViewerWithNavigation
      v-if="documentDetail && documentDetail.file_url"
      :id="id"
      class="w-1/2"
      :auto-fit="true"
      :file-name="documentDetail.file_name"
      :fileURL="documentDetail.file_url"
    />
  </div>
</template>

